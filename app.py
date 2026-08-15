from flask import Flask, render_template, redirect, url_for, flash, request, session, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from functools import wraps
import os
import secrets
import bcrypt
import json
import math
import random
import re
import smtplib
import numpy as np 
from flask_mail import Mail, Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from collections import Counter

from utils.modern_crypto import aes_decrypt, aes_encrypt
from utils.rsa import ciphertext_to_string, generate_keypair, rsa_decrypt, rsa_encrypt
from flask_migrate import Migrate


# =============== INISIALISASI APLIKASI ===============
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crypto.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800
app.config.update(
    MAIL_SERVER='sandbox.smtp.mailtrap.io',
    MAIL_PORT=2525,
    MAIL_USERNAME='8af2cb84cfc5b6',         
    MAIL_PASSWORD='d1620a3c08deea',       
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_DEFAULT_SENDER=('DecoDify', 'noreply@decodify.com')
)
mail = Mail(app)

# Inisialisasi ekstensi
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Anda harus login terlebih dahulu untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'
login_manager.refresh_view = "login"
login_manager.needs_refresh_message = "Session expired, please login again"
login_manager.needs_refresh_message_category = "warning"

# Argon2 hasher 
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# =============== CONTEXT PROCESSOR ===============
@app.context_processor
@app.context_processor
def inject_user_data():
    """Inject user data into all templates"""
    user_data = {}
    
    if current_user.is_authenticated:
        progress = get_user_progress(current_user.id)
        
        # Get counts
        learning_count = UserActivity.query.filter_by(
            user_id=current_user.id, 
            activity_type='learning'
        ).count()
        
        cipher_count = CipherUsage.query.filter_by(user_id=current_user.id).count()
        
        challenge_count = ChallengeAttempt.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).count()
        
        completed_ciphers = CipherUsage.query.filter_by(
            user_id=current_user.id
        ).filter(CipherUsage.usage_count >= 3).count()
        
        # Get unread notifications count
        unread_notifications = get_unread_notifications_count(current_user.id)
        
        # Default weather data
        weather_temp = 28
        
        user_data = {
            'username': current_user.username,
            'user_avatar': current_user.avatar,
            'is_premium': current_user.has_active_premium if hasattr(current_user, 'has_active_premium') else False,
            'learning_count': learning_count,
            'cipher_count': cipher_count,
            'challenge_count': challenge_count,
            'completed_ciphers': completed_ciphers,
            'user_level': progress.level if progress else 1,
            'user_xp': progress.xp if progress else 0,
            'streak_days': progress.current_streak if progress else 0,
            'current_user': current_user,
            'unread_notifications': unread_notifications,
            'weather_temp': weather_temp
        }
    else:
        user_data = {
            'username': 'Guest',
            'user_avatar': None,
            'is_premium': False,
            'learning_count': 0,
            'cipher_count': 0,
            'challenge_count': 0,
            'completed_ciphers': 0,
            'user_level': 1,
            'user_xp': 0,
            'streak_days': 0,
            'current_user': None,
            'unread_notifications': 0,
            'weather_temp': 28
        }
    
    return user_data

# =============== MODELS ===============
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    premium_expires = db.Column(db.DateTime, nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """Hash password menggunakan Argon2"""
        self.password_hash = ph.hash(password)
    
    def check_password(self, password):
        """Verifikasi password dengan Argon2"""
        try:
            ph.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    @property
    def has_active_premium(self):
        """Check if user has active premium subscription"""
        if not self.is_premium:
            return False
        if not self.premium_expires:
            return True
        return datetime.utcnow() < self.premium_expires
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, order_by='Notification.created_at.desc()'))

class LearningModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    category = db.Column(db.String(50))
    difficulty = db.Column(db.String(20), default='beginner')
    estimated_time = db.Column(db.Integer)
    order = db.Column(db.Integer, default=0)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# =============== MODELS TUTORIAL ===============
class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default='beginner')
    duration_minutes = db.Column(db.Integer, default=30)
    category = db.Column(db.String(50))
    tags = db.Column(db.String(200))
    is_premium = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    estimated_reading_time = db.Column(db.Integer, default=10)
    order = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())

class TutorialCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(20))
    is_premium = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    tutorial_count = db.Column(db.Integer, default=0)

class TutorialReference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(100))
    icon = db.Column(db.String(50))
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    tutorial = db.relationship('Tutorial', backref=db.backref('references', lazy=True))

class UserTutorialProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    progress_percentage = db.Column(db.Integer, default=0)
    time_spent_minutes = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    completed_at = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('tutorial_progress', lazy=True))
    tutorial = db.relationship('Tutorial', backref=db.backref('user_progress', lazy=True))

class UserModuleProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_module.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    completed_at = db.Column(db.DateTime, nullable=True)
    time_spent = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref=db.backref('module_progress', lazy=True))
    module = db.relationship('LearningModule', backref=db.backref('user_progress', lazy=True))

# Tambahkan model VideoCourse sebelum UserVideoProgress
class VideoCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.Integer, default=0)  # in seconds
    thumbnail = db.Column(db.String(500))
    instructor = db.Column(db.String(100))
    category = db.Column(db.String(50))
    difficulty = db.Column(db.String(20), default='beginner')
    is_premium = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())

class UserVideoProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video_course.id'), nullable=False)
    watched = db.Column(db.Boolean, default=False)
    progress = db.Column(db.Integer, default=0)
    last_position = db.Column(db.Integer, default=0)
    last_watched = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('video_progress', lazy=True))
    video = db.relationship('VideoCourse', backref=db.backref('user_progresss', lazy=True))

class GlossaryTerm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    example = db.Column(db.Text)
    related_terms = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    cipher_name = db.Column(db.String(50))
    xp_gained = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    challenges_completed = db.Column(db.Integer, default=0)
    encryptions_performed = db.Column(db.Integer, default=0)
    learning_time_minutes = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date, default=db.func.current_date())
    
    user = db.relationship('User', backref=db.backref('progress', uselist=False))

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))
    xp_reward = db.Column(db.Integer, default=100)
    requirement = db.Column(db.String(100))

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('user_achievements', lazy=True))
    achievement = db.relationship('Achievement', backref=db.backref('user_achievements', lazy=True))

class CipherUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cipher_name = db.Column(db.String(50), nullable=False)
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('cipher_usages', lazy=True))

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cipher_name = db.Column(db.String(50), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.String(1000))
    difficulty = db.Column(db.String(20), default='medium')
    xp_reward = db.Column(db.Integer, default=10)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cipher_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('quiz_attempts', lazy=True))

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cipher_name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    ciphertext = db.Column(db.String(500), nullable=False)
    plaintext = db.Column(db.String(500), nullable=False)
    hint = db.Column(db.String(200))
    difficulty = db.Column(db.String(20), default='easy')
    xp_reward = db.Column(db.Integer, default=25)
    category = db.Column(db.String(50))

class ChallengeAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    attempts = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref=db.backref('challenge_attempts', lazy=True))
    challenge = db.relationship('Challenge', backref=db.backref('attempts', lazy=True))

# =============== UTILITAS ===============
@login_manager.user_loader
def load_user(user_id):
    """Load user dari database"""
    try:
        user = User.query.get(int(user_id))
        print(f"DEBUG - User_loader called with ID: {user_id}, Found: {user is not None}")
        return user
    except Exception as e:
        print(f"DEBUG - Error in user_loader: {e}")
        return None

def secure_logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Anda sudah logout.', 'info')
            return redirect(url_for('index'))
        
        if request.method != 'POST':
            flash('Gunakan tombol logout (POST).', 'warning')
            return redirect(url_for('dashboard'))
        
        token = request.form.get('token')
        if not token or token != session.get('logout_token'):
            flash('Akses tidak valid. Gunakan tombol logout yang disediakan.', 'danger')
            return redirect(url_for('dashboard'))
        
        session.pop('logout_token', None)
        return f(*args, **kwargs)
    return decorated_function

def send_reset_email(user_email, reset_token):
    """Kirim email reset password"""
    reset_url = url_for('reset_password', token=reset_token, _external=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Reset Password DecoDify</h1>
            </div>
            <div class="content">
                <h2>Halo!</h2>
                <p>Kami menerima permintaan reset password untuk akun DecoDify Anda.</p>
                <p>Klik tombol di bawah ini untuk membuat password baru:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </div>
                
                <p>Atau copy link berikut ke browser Anda:</p>
                <p style="background: #e2e8f0; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_url}
                </p>
                
                <p><strong>⚠️ Link ini akan kadaluarsa dalam 1 jam.</strong></p>
                
                <p>Jika Anda tidak meminta reset password, abaikan email ini.</p>
                
                <div class="footer">
                    <p>Terima kasih,<br>Tim DecoDify</p>
                    <p style="font-size: 12px; color: #94a3b8;">
                        Email ini dikirim secara otomatis. Mohon tidak membalas email ini.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Reset Password DecoDify
    
    Klik link berikut untuk reset password:
    {reset_url}
    
    Link akan kadaluarsa dalam 1 jam.
    
    Jika Anda tidak meminta reset password, abaikan email ini.
    
    Terima kasih,
    Tim DecoDify
    """
    
    try:
        msg = Message(
            subject="Reset Password - DecoDify",
            recipients=[user_email],
            html=html_content,
            body=text_content
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def create_notification(user_id, title, message, notification_type='info', link=None, expires_in_hours=24):
    """Buat notifikasi baru untuk user"""
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours) if expires_in_hours else None
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        expires_at=expires_at
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return notification

def get_unread_notifications_count(user_id):
    """Hitung jumlah notifikasi yang belum dibaca"""
    count = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).filter(
        Notification.expires_at.is_(None) | (Notification.expires_at > datetime.utcnow())
    ).count()
    
    return count

def get_user_notifications(user_id, limit=10):
    """Dapatkan notifikasi user"""
    notifications = Notification.query.filter_by(
        user_id=user_id
    ).filter(
        Notification.expires_at.is_(None) | (Notification.expires_at > datetime.utcnow())
    ).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    return notifications

# =============== CIPHER UTILITIES ===============
def caesar_encrypt(text, shift):
    """Enkripsi teks menggunakan Caesar Cipher"""
    result = ""
    shift = shift % 26
    
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shifted = (ord(char) - base + shift) % 26
            result += chr(base + shifted)
        else:
            result += char
    
    return result

def caesar_decrypt(text, shift):
    """Dekripsi teks yang dienkripsi dengan Caesar Cipher"""
    return caesar_encrypt(text, -shift)

def caesar_crack(ciphertext):
    """Bruteforce Caesar Cipher"""
    results = []
    for shift in range(26):
        decrypted = caesar_decrypt(ciphertext, shift)
        results.append({
            'shift': shift,
            'text': decrypted
        })
    return results

def vigenere_encrypt(plaintext, key):
    """Encrypt plaintext using Vigenere cipher"""
    result = []
    key = key.upper()
    key_index = 0
    
    for char in plaintext:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            base = ord('A') if char.isupper() else ord('a')
            encrypted_char = chr((ord(char) - base + shift) % 26 + base)
            result.append(encrypted_char)
            key_index += 1
        else:
            result.append(char)
    
    return ''.join(result)

def vigenere_decrypt(ciphertext, key):
    """Decrypt ciphertext using Vigenere cipher"""
    result = []
    key = key.upper()
    key_index = 0
    
    for char in ciphertext:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            base = ord('A') if char.isupper() else ord('a')
            decrypted_char = chr((ord(char) - base - shift) % 26 + base)
            result.append(decrypted_char)
            key_index += 1
        else:
            result.append(char)
    
    return ''.join(result)

def vigenere_analyze(ciphertext):
    """Analisis sederhana untuk Vigenere Cipher"""
    ciphertext_clean = ''.join(c for c in ciphertext.upper() if c.isalpha())
    
    if not ciphertext_clean:
        return {
            'length': 0,
            'alphabetic_chars': 0,
            'top_5_chars': [],
            'warning': 'Teks tidak mengandung huruf alfabet'
        }
    
    freq = Counter(ciphertext_clean)
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    n = len(ciphertext_clean)
    ic = sum(f * (f - 1) for f in freq.values()) / (n * (n - 1)) if n > 1 else 0
    
    estimated_length = 0
    if ic > 0:
        expected_ic_english = 0.067
        expected_ic_random = 0.038
        estimated_length = int((0.027 * n) / ((n - 1) * ic - expected_ic_random * n + expected_ic_english))
        estimated_length = max(1, min(estimated_length, 20))
    
    sequences = {}
    for length in range(3, 7):
        for i in range(len(ciphertext_clean) - length + 1):
            sequence = ciphertext_clean[i:i + length]
            positions = [m.start() for m in re.finditer(re.escape(sequence), ciphertext_clean)]
            
            if len(positions) > 1:
                sequences[sequence] = {
                    'sequence': sequence,
                    'positions': positions,
                    'occurrences': len(positions)
                }
    
    repeating_sequences = sorted(
        sequences.values(), 
        key=lambda x: x['occurrences'], 
        reverse=True
    )[:10]
    
    return {
        'length': len(ciphertext),
        'alphabetic_chars': n,
        'top_5_chars': sorted_freq[:5],
        'index_of_coincidence': round(ic, 4),
        'estimated_key_length': estimated_length,
        'repeating_sequences': repeating_sequences,
        'most_common_letter': sorted_freq[0][0] if sorted_freq else None,
        'english_ic_comparison': round(ic / 0.067, 2) if ic > 0 else 0
    }

# Playfair Cipher Utilities
def prepare_playfair_key(key):
    """Persiapan kunci untuk Playfair Cipher"""
    key = ''.join(filter(str.isalpha, key.upper()))
    key = key.replace('J', 'I')
    
    unique_chars = []
    for char in key:
        if char not in unique_chars:
            unique_chars.append(char)
    
    return ''.join(unique_chars)

def create_playfair_matrix(key):
    """Buat matriks 5x5 untuk Playfair Cipher"""
    prepared_key = prepare_playfair_key(key)
    alphabet = 'ABCDEFGHIKLMNOPQRSTUVWXYZ'
    
    matrix_chars = []
    used_chars = set()
    
    for char in prepared_key:
        if char not in used_chars:
            matrix_chars.append(char)
            used_chars.add(char)
    
    for char in alphabet:
        if char not in used_chars:
            matrix_chars.append(char)
            used_chars.add(char)
    
    return [matrix_chars[i:i+5] for i in range(0, 25, 5)]

def find_char_position(matrix, char):
    """Cari posisi karakter dalam matriks Playfair"""
    char = char.upper().replace('J', 'I')
    for row in range(5):
        for col in range(5):
            if matrix[row][col] == char:
                return (row, col)
    return None

def prepare_playfair_text(text, mode='encrypt'):
    """Persiapan teks untuk Playfair Cipher"""
    text = ''.join(filter(str.isalpha, text.upper()))
    text = text.replace('J', 'I')
    
    digraphs = []
    i = 0
    
    while i < len(text):
        if i + 1 < len(text):
            a = text[i]
            b = text[i + 1]
            
            if a == b:
                digraphs.append(a + 'X')
                i += 1
            else:
                digraphs.append(a + b)
                i += 2
        else:
            digraphs.append(text[i] + 'X')
            i += 1
    
    if mode == 'decrypt' and digraphs:
        last_digraph = digraphs[-1]
        if last_digraph.endswith('X'):
            digraphs[-1] = last_digraph[0]
            if len(last_digraph) > 1 and last_digraph[1] == 'X':
                digraphs[-1] = last_digraph[0]
    
    return digraphs

def playfair_encrypt_decrypt(text, key, mode='encrypt'):
    """Enkripsi atau dekripsi menggunakan Playfair Cipher"""
    matrix = create_playfair_matrix(key)
    digraphs = prepare_playfair_text(text, mode)
    
    result = ''
    
    for digraph in digraphs:
        if len(digraph) < 2:
            result += digraph
            continue
        
        char1, char2 = digraph[0], digraph[1]
        pos1 = find_char_position(matrix, char1)
        pos2 = find_char_position(matrix, char2)
        
        if not pos1 or not pos2:
            result += digraph
            continue
        
        row1, col1 = pos1
        row2, col2 = pos2
        
        if row1 == row2:
            if mode == 'encrypt':
                new_col1 = (col1 + 1) % 5
                new_col2 = (col2 + 1) % 5
            else:
                new_col1 = (col1 - 1) % 5
                new_col2 = (col2 - 1) % 5
            new_char1 = matrix[row1][new_col1]
            new_char2 = matrix[row2][new_col2]
        
        elif col1 == col2:
            if mode == 'encrypt':
                new_row1 = (row1 + 1) % 5
                new_row2 = (row2 + 1) % 5
            else:
                new_row1 = (row1 - 1) % 5
                new_row2 = (row2 - 1) % 5
            new_char1 = matrix[new_row1][col1]
            new_char2 = matrix[new_row2][col2]
        
        else:
            new_char1 = matrix[row1][col2]
            new_char2 = matrix[row2][col1]
        
        result += new_char1 + new_char2
    
    return result

def playfair_encrypt(plaintext, key):
    """Enkripsi teks menggunakan Playfair Cipher"""
    return playfair_encrypt_decrypt(plaintext, key, 'encrypt')

def playfair_decrypt(ciphertext, key):
    """Dekripsi teks yang dienkripsi dengan Playfair Cipher"""
    return playfair_encrypt_decrypt(ciphertext, key, 'decrypt')

def analyze_playfair_key(key):
    """Analisis kunci Playfair"""
    prepared_key = prepare_playfair_key(key)
    matrix = create_playfair_matrix(key)
    
    return {
        'original_key': key,
        'prepared_key': prepared_key,
        'key_length': len(prepared_key),
        'unique_chars': len(set(prepared_key)),
        'matrix': matrix
    }

# Bruteforce Utilities
def calculate_english_score(text):
    """Hitung score berdasarkan frekuensi karakter bahasa Inggris"""
    common_chars = 'ETAOINSHRDLCUMWFGYPBVKJXQZ'
    score = 0
    text_upper = text.upper()
    
    score += text.count(' ') * 2
    
    for i, char in enumerate(common_chars):
        if char in text_upper:
            score += (26 - i) * text_upper.count(char)
    
    return score

def bruteforce_caesar(ciphertext):
    """Bruteforce Caesar Cipher"""
    results = []
    for shift in range(26):
        decrypted = caesar_decrypt(ciphertext, shift)
        score = calculate_english_score(decrypted)
        results.append({
            'shift': shift,
            'text': decrypted,
            'score': score
        })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# Substitution Cipher Utilities
def substitution_encrypt(text, key):
    """Encrypt text using Substitution Cipher"""
    result = []
    
    # Validate key
    if len(key) != 26 or not key.isalpha():
        raise ValueError("Key must be 26 uppercase letters (A-Z)")
    
    # Create encryption mapping
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    encrypt_map = {alphabet[i]: key[i] for i in range(26)}
    
    for char in text:
        if char.isalpha():
            is_upper = char.isupper()
            char_upper = char.upper()
            if char_upper in encrypt_map:
                encrypted_char = encrypt_map[char_upper]
                result.append(encrypted_char if is_upper else encrypted_char.lower())
            else:
                result.append(char)
        else:
            result.append(char)
    
    return ''.join(result)

def substitution_decrypt(text, key):
    """Decrypt text using Substitution Cipher"""
    result = []
    
    # Validate key
    if len(key) != 26 or not key.isalpha():
        raise ValueError("Key must be 26 uppercase letters (A-Z)")
    
    # Create decryption mapping
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    decrypt_map = {key[i]: alphabet[i] for i in range(26)}
    
    for char in text:
        if char.isalpha():
            is_upper = char.isupper()
            char_upper = char.upper()
            if char_upper in decrypt_map:
                decrypted_char = decrypt_map[char_upper]
                result.append(decrypted_char if is_upper else decrypted_char.lower())
            else:
                result.append(char)
        else:
            result.append(char)
    
    return ''.join(result)

def generate_substitution_key(keyword=""):
    """Generate substitution key from keyword or random"""
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    if keyword:
        # Remove duplicates while preserving order
        unique_keyword = ""
        for char in keyword.upper():
            if char.isalpha() and char not in unique_keyword:
                unique_keyword += char
        
        # Fill remaining letters
        remaining = [c for c in alphabet if c not in unique_keyword]
        random.shuffle(remaining)
        return unique_keyword + ''.join(remaining)
    else:
        # Generate random key
        chars = list(alphabet)
        random.shuffle(chars)
        return ''.join(chars)

def rail_fence_decrypt(ciphertext, rails):
    """Decrypt text using Rail Fence cipher"""
    if rails < 2 or rails > 10:
        raise ValueError("Rails must be between 2 and 10")
    
    # Create fence pattern
    fence = [[None] * len(ciphertext) for _ in range(rails)]
    
    rail = 0
    direction = 1
    for i in range(len(ciphertext)):
        fence[rail][i] = '*'
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction = -direction
    
    # Fill fence with ciphertext
    index = 0
    for i in range(rails):
        for j in range(len(ciphertext)):
            if fence[i][j] == '*' and index < len(ciphertext):
                fence[i][j] = ciphertext[index]
                index += 1
    
    # Read the fence
    result = []
    rail = 0
    direction = 1
    for i in range(len(ciphertext)):
        if fence[rail][i] is not None:
            result.append(fence[rail][i])
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction = -direction
    
    return ''.join(result)

def columnar_transposition_encrypt(text, key):
    """Encrypt text using Columnar Transposition"""
    # Clean key
    key_clean = key.upper().replace(' ', '')
    if not key_clean:
        raise ValueError("Key cannot be empty")
    
    # Determine column order
    columns = len(key_clean)
    rows = (len(text) + columns - 1) // columns
    
    # Create grid
    grid = [[''] * columns for _ in range(rows)]
    
    # Fill grid row by row
    text_index = 0
    for r in range(rows):
        for c in range(columns):
            if text_index < len(text):
                grid[r][c] = text[text_index]
                text_index += 1
            else:
                grid[r][c] = 'X'  # Padding
    
    # Determine column order based on key
    key_order = [(key_clean[i], i) for i in range(columns)]
    key_order.sort(key=lambda x: x[0])
    
    # Read columns in key order
    result = []
    for _, col_index in key_order:
        for r in range(rows):
            result.append(grid[r][col_index])
    
    return ''.join(result)

def columnar_transposition_decrypt(ciphertext, key):
    """Decrypt text using Columnar Transposition"""
    # Clean key
    key_clean = key.upper().replace(' ', '')
    if not key_clean:
        raise ValueError("Key cannot be empty")
    
    columns = len(key_clean)
    rows = len(ciphertext) // columns
    
    # Determine column order
    key_order = [(key_clean[i], i) for i in range(columns)]
    key_order.sort(key=lambda x: x[0])
    
    # Create grid
    grid = [[''] * columns for _ in range(rows)]
    
    # Fill grid column by column in key order
    ciphertext_index = 0
    for _, col_index in key_order:
        for r in range(rows):
            if ciphertext_index < len(ciphertext):
                grid[r][col_index] = ciphertext[ciphertext_index]
                ciphertext_index += 1
    
    # Read grid row by row
    result = []
    for r in range(rows):
        for c in range(columns):
            result.append(grid[r][c])
    
    # Remove padding
    plaintext = ''.join(result).rstrip('X')
    return plaintext

def route_cipher_encrypt(text, rows, cols, pattern='column'):
    """Encrypt text using Route Cipher"""
    # Clean text
    text_clean = text.replace(' ', '').upper()
    
    # Create grid
    grid = [[''] * cols for _ in range(rows)]
    
    # Fill grid
    text_index = 0
    for r in range(rows):
        for c in range(cols):
            if text_index < len(text_clean):
                grid[r][c] = text_clean[text_index]
                text_index += 1
            else:
                grid[r][c] = 'X'  # Padding
    
    result = []
    
    if pattern == 'column':
        # Read column by column
        for c in range(cols):
            for r in range(rows):
                result.append(grid[r][c])
    elif pattern == 'row':
        # Read row by row
        for r in range(rows):
            for c in range(cols):
                result.append(grid[r][c])
    elif pattern == 'spiral':
        # Read in spiral pattern
        top, bottom = 0, rows - 1
        left, right = 0, cols - 1
        
        while top <= bottom and left <= right:
            # Right
            for c in range(left, right + 1):
                result.append(grid[top][c])
            top += 1
            
            # Down
            for r in range(top, bottom + 1):
                result.append(grid[r][right])
            right -= 1
            
            # Left
            if top <= bottom:
                for c in range(right, left - 1, -1):
                    result.append(grid[bottom][c])
                bottom -= 1
            
            # Up
            if left <= right:
                for r in range(bottom, top - 1, -1):
                    result.append(grid[r][left])
                left += 1
    
    return ''.join(result)

def route_cipher_decrypt(ciphertext, rows, cols, pattern='column'):
    """Decrypt text using Route Cipher"""
    # Create empty grid
    grid = [[''] * cols for _ in range(rows)]
    
    ciphertext_chars = list(ciphertext)
    
    if pattern == 'column':
        # Fill column by column
        for c in range(cols):
            for r in range(rows):
                if ciphertext_chars:
                    grid[r][c] = ciphertext_chars.pop(0)
    elif pattern == 'row':
        # Fill row by row
        for r in range(rows):
            for c in range(cols):
                if ciphertext_chars:
                    grid[r][c] = ciphertext_chars.pop(0)
    elif pattern == 'spiral':
        # Fill in spiral pattern
        top, bottom = 0, rows - 1
        left, right = 0, cols - 1
        
        while top <= bottom and left <= right and ciphertext_chars:
            # Right
            for c in range(left, right + 1):
                if ciphertext_chars:
                    grid[top][c] = ciphertext_chars.pop(0)
            top += 1
            
            # Down
            for r in range(top, bottom + 1):
                if ciphertext_chars:
                    grid[r][right] = ciphertext_chars.pop(0)
            right -= 1
            
            # Left
            if top <= bottom:
                for c in range(right, left - 1, -1):
                    if ciphertext_chars:
                        grid[bottom][c] = ciphertext_chars.pop(0)
                bottom -= 1
            
            # Up
            if left <= right:
                for r in range(bottom, top - 1, -1):
                    if ciphertext_chars:
                        grid[r][left] = ciphertext_chars.pop(0)
                left += 1
    
    # Read grid row by row
    result = []
    for r in range(rows):
        for c in range(cols):
            result.append(grid[r][c])
    
    # Remove padding
    plaintext = ''.join(result).rstrip('X')
    return plaintext

def spiral_cipher_encrypt(text, size):
    """Encrypt text using Spiral Cipher"""
    text_clean = text.replace(' ', '').upper()
    
    # Create empty grid
    grid = [[''] * size for _ in range(size)]
    
    # Fill grid in spiral pattern (clockwise, from outside in)
    top, bottom = 0, size - 1
    left, right = 0, size - 1
    text_index = 0
    
    while top <= bottom and left <= right and text_index < len(text_clean):
        # Right
        for c in range(left, right + 1):
            if text_index < len(text_clean):
                grid[top][c] = text_clean[text_index]
                text_index += 1
        top += 1
        
        # Down
        for r in range(top, bottom + 1):
            if text_index < len(text_clean):
                grid[r][right] = text_clean[text_index]
                text_index += 1
        right -= 1
        
        # Left
        if top <= bottom:
            for c in range(right, left - 1, -1):
                if text_index < len(text_clean):
                    grid[bottom][c] = text_clean[text_index]
                    text_index += 1
            bottom -= 1
        
        # Up
        if left <= right:
            for r in range(bottom, top - 1, -1):
                if text_index < len(text_clean):
                    grid[r][left] = text_clean[text_index]
                text_index += 1
            left += 1
    
    # Read grid row by row for ciphertext
    result = []
    for r in range(size):
        for c in range(size):
            if grid[r][c]:
                result.append(grid[r][c])
            else:
                result.append('X')  # Padding
    
    return ''.join(result)

def spiral_cipher_decrypt(ciphertext, size):
    """Decrypt text using Spiral Cipher"""
    # Create empty grid
    grid = [[''] * size for _ in range(size)]
    
    # Fill grid row by row with ciphertext
    ciphertext_chars = list(ciphertext)
    for r in range(size):
        for c in range(size):
            if ciphertext_chars:
                grid[r][c] = ciphertext_chars.pop(0)
    
    # Read grid in spiral pattern
    result = []
    top, bottom = 0, size - 1
    left, right = 0, size - 1
    
    while top <= bottom and left <= right:
        # Right
        for c in range(left, right + 1):
            result.append(grid[top][c])
        top += 1
        
        # Down
        for r in range(top, bottom + 1):
            result.append(grid[r][right])
        right -= 1
        
        # Left
        if top <= bottom:
            for c in range(right, left - 1, -1):
                result.append(grid[bottom][c])
            bottom -= 1
        
        # Up
        if left <= right:
            for r in range(bottom, top - 1, -1):
                result.append(grid[r][left])
            left += 1
    
    # Remove padding and return
    plaintext = ''.join(result).rstrip('X')
    return plaintext

# =============== HILL CIPHER UTILITIES ===============
def prepare_hill_text(text, block_size):
    """Persiapan teks untuk Hill Cipher"""
    # Hanya huruf kapital
    text = ''.join(c.upper() for c in text if c.isalpha())
    
    # Padding jika panjang tidak kelipatan block_size
    if len(text) % block_size != 0:
        padding_needed = block_size - (len(text) % block_size)
        text += 'X' * padding_needed
    
    return text

def convert_text_to_numbers(text):
    """Konversi teks ke angka (A=0, B=1, ..., Z=25)"""
    return [ord(char) - 65 for char in text]

def convert_numbers_to_text(numbers):
    """Konversi angka ke teks"""
    return ''.join(chr(num + 65) for num in numbers)

def validate_hill_key(matrix):
    """Validasi matriks kunci Hill Cipher"""
    size = len(matrix)
    
    # Cek apakah matriks persegi
    if any(len(row) != size for row in matrix):
        return False, "Matriks harus persegi"
    
    # Cek semua elemen antara 0-25
    for row in matrix:
        for val in row:
            if not (0 <= val <= 25):
                return False, "Semua elemen matriks harus antara 0-25"
    
    # Hitung determinan
    det = calculate_matrix_determinant(matrix)
    
    # Cek apakah determinan coprime dengan 26
    if not is_coprime(det, 26):
        return False, f"Determinan ({det}) harus coprime dengan 26"
    
    return True, "Matriks valid"

def calculate_matrix_determinant(matrix):
    """Hitung determinan matriks"""
    size = len(matrix)
    
    if size == 2:
        # 2x2 matrix: ad - bc
        a, b = matrix[0][0], matrix[0][1]
        c, d = matrix[1][0], matrix[1][1]
        return (a * d - b * c) % 26
    
    elif size == 3:
        # 3x3 matrix: a(ei - fh) - b(di - fg) + c(dh - eg)
        a, b, c = matrix[0][0], matrix[0][1], matrix[0][2]
        d, e, f = matrix[1][0], matrix[1][1], matrix[1][2]
        g, h, i = matrix[2][0], matrix[2][1], matrix[2][2]
        
        return (a*(e*i - f*h) - b*(d*i - f*g) + c*(d*h - e*g)) % 26
    
    return 0

def is_coprime(a, b):
    """Cek apakah dua bilangan coprime (GCD = 1)"""
    while b != 0:
        a, b = b, a % b
    return a == 1

def mod_inverse(a, m=26):
    """Cari invers modulo m"""
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return None

def calculate_matrix_mod_inverse(matrix):
    """Hitung invers matriks modulo 26"""
    size = len(matrix)
    
    # Hitung determinan
    det = calculate_matrix_determinant(matrix)
    if det < 0:
        det += 26
    
    # Cari invers determinan
    det_inv = mod_inverse(det, 26)
    if det_inv is None:
        return None
    
    if size == 2:
        # Invers matriks 2x2
        a, b = matrix[0][0], matrix[0][1]
        c, d = matrix[1][0], matrix[1][1]
        
        # Matriks adjoint
        adj = [[d, -b], [-c, a]]
        
        # Kalikan dengan invers determinan
        inv_matrix = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                inv_matrix[i][j] = (adj[i][j] * det_inv) % 26
                if inv_matrix[i][j] < 0:
                    inv_matrix[i][j] += 26
        
        return inv_matrix
    
    elif size == 3:
        # Invers matriks 3x3 lebih kompleks
        a, b, c = matrix[0][0], matrix[0][1], matrix[0][2]
        d, e, f = matrix[1][0], matrix[1][1], matrix[1][2]
        g, h, i = matrix[2][0], matrix[2][1], matrix[2][2]
        
        # Matriks kofaktor
        cofactor = [
            [(e*i - f*h) % 26, (f*g - d*i) % 26, (d*h - e*g) % 26],
            [(c*h - b*i) % 26, (a*i - c*g) % 26, (b*g - a*h) % 26],
            [(b*f - c*e) % 26, (c*d - a*f) % 26, (a*e - b*d) % 26]
        ]
        
        # Transpose (adjoint)
        adj = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for row in range(3):
            for col in range(3):
                adj[col][row] = cofactor[row][col]
        
        # Kalikan dengan invers determinan
        inv_matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for row in range(3):
            for col in range(3):
                inv_matrix[row][col] = (adj[row][col] * det_inv) % 26
        
        return inv_matrix
    
    return None

def matrix_multiply(matrix, vector):
    """Perkalian matriks dengan vektor modulo 26"""
    size = len(matrix)
    result = [0] * size
    
    for i in range(size):
        for j in range(size):
            result[i] += matrix[i][j] * vector[j]
        result[i] %= 26
    
    return result

def hill_encrypt(plaintext, key_matrix):
    """Enkripsi teks menggunakan Hill Cipher"""
    # Persiapkan teks
    size = len(key_matrix)
    prepared_text = prepare_hill_text(plaintext, size)
    
    # Konversi teks ke angka
    numbers = convert_text_to_numbers(prepared_text)
    
    # Enkripsi per blok
    encrypted_numbers = []
    for i in range(0, len(numbers), size):
        block = numbers[i:i+size]
        encrypted_block = matrix_multiply(key_matrix, block)
        encrypted_numbers.extend(encrypted_block)
    
    # Konversi kembali ke teks
    return convert_numbers_to_text(encrypted_numbers)

def hill_decrypt(ciphertext, key_matrix):
    """Dekripsi teks menggunakan Hill Cipher"""
    # Persiapkan teks
    size = len(key_matrix)
    prepared_text = prepare_hill_text(ciphertext, size)
    
    # Cari invers matriks
    inv_matrix = calculate_matrix_mod_inverse(key_matrix)
    if inv_matrix is None:
        raise ValueError("Matriks tidak invertible modulo 26")
    
    # Konversi teks ke angka
    numbers = convert_text_to_numbers(prepared_text)
    
    # Dekripsi per blok
    decrypted_numbers = []
    for i in range(0, len(numbers), size):
        block = numbers[i:i+size]
        decrypted_block = matrix_multiply(inv_matrix, block)
        decrypted_numbers.extend(decrypted_block)
    
    # Konversi kembali ke teks
    return convert_numbers_to_text(decrypted_numbers)

def analyze_hill_key(matrix):
    """Analisis matriks kunci Hill Cipher"""
    size = len(matrix)
    det = calculate_matrix_determinant(matrix)
    valid, message = validate_hill_key(matrix)
    
    return {
        'size': f"{size}x{size}",
        'determinant': det,
        'is_valid': valid,
        'message': message,
        'invertible': mod_inverse(det, 26) is not None,
        'matrix': matrix
    }

# =============== FUNGSI HELPER ===============
def get_time_ago(dt):
    """Format waktu relatif (misal: 5 menit yang lalu)"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        return f'{diff.days // 365} tahun lalu'
    elif diff.days > 30:
        return f'{diff.days // 30} bulan lalu'
    elif diff.days > 0:
        return f'{diff.days} hari lalu'
    elif diff.seconds > 3600:
        return f'{diff.seconds // 3600} jam lalu'
    elif diff.seconds > 60:
        return f'{diff.seconds // 60} menit lalu'
    else:
        return 'Baru saja'

def get_user_progress(user_id):
    """Get or create user progress"""
    progress = UserProgress.query.filter_by(user_id=user_id).first()
    if not progress:
        progress = UserProgress(user_id=user_id)
        db.session.add(progress)
        db.session.commit()
    return progress

def get_learn_data(user_id):
    """Get learning data for learn page"""
    user = User.query.get(user_id)
    if not user:
        return None
    
    progress = get_user_progress(user_id)
    
    # Get learning module stats
    learning_activities = UserActivity.query.filter_by(
        user_id=user_id, 
        activity_type='learning'
    ).all()
    
    # Count completed modules
    completed_modules = len([a for a in learning_activities if 'module' in a.description.lower()])
    total_modules = 12
    
    # Get learning time in hours
    learning_time_hours = progress.learning_time_minutes // 60
    
    # Get cipher usage stats
    cipher_usages = CipherUsage.query.filter_by(user_id=user_id).all()
    cipher_count = len(cipher_usages)
    
    # Get challenge stats
    completed_challenges = ChallengeAttempt.query.filter_by(
        user_id=user_id,
        completed=True
    ).count()
    
    # Video course stats
    video_count = 9
    premium_videos = 3 if user.is_premium else 0
    
    # Calculate progress percentage
    progress_percentage = min(100, int((completed_modules / total_modules) * 100)) if total_modules > 0 else 0
    
    return {
        'username': user.username,
        'is_premium': user.is_premium,
        'completed_modules': completed_modules,
        'total_modules': total_modules,
        'progress_percentage': progress_percentage,
        'total_study_hours': learning_time_hours,
        'streak_days': progress.current_streak,
        'cipher_count': cipher_count,
        'completed_ciphers': len([c for c in cipher_usages if c.usage_count >= 3]),
        'challenge_count': completed_challenges,
        'user_level': progress.level,
        'user_xp': progress.xp,
        'learning_count': len(learning_activities),
        'video_count': video_count,
        'premium_videos': premium_videos,
        'video_hours': '5.5',
        'module_count': 6,
        'term_count': 24,
        'categories': 5,
        'user_avatar': user.avatar
    }

def get_user_data(user_id):
    """Get all user data for templates"""
    user = User.query.get(user_id)
    if not user:
        return None
    
    progress = get_user_progress(user_id)
    
    # Get counts from database
    learning_count = UserActivity.query.filter_by(
        user_id=user_id, 
        activity_type='learning'
    ).count()
    
    cipher_count = CipherUsage.query.filter_by(user_id=user_id).count()
    
    challenge_count = ChallengeAttempt.query.filter_by(
        user_id=user_id,
        completed=True
    ).count()
    
    completed_ciphers = CipherUsage.query.filter_by(
        user_id=user_id
    ).filter(CipherUsage.usage_count >= 3).count()
    
    return {
        'username': user.username,
        'email': user.email,
        'is_premium': user.has_active_premium if hasattr(user, 'has_active_premium') else False,
        'user_level': progress.level,
        'user_xp': progress.xp,
        'streak_days': progress.current_streak,
        'learning_count': learning_count,
        'cipher_count': cipher_count,
        'challenge_count': challenge_count,
        'completed_ciphers': completed_ciphers,
        'progress_percentage': min(100, int((completed_ciphers / 13) * 100)) if 13 > 0 else 0,
        'user_avatar': user.avatar,
        'weather_temp': '28',
        'unread_notifications': 0
    }

def get_dashboard_data(user_id):
    """Get comprehensive dashboard data for user"""
    progress = get_user_progress(user_id)
    
    # Get cipher usage stats
    cipher_usages = CipherUsage.query.filter_by(user_id=user_id).all()
    completed_ciphers = len(cipher_usages)
    total_ciphers = 13
    
    # Calculate progress percentage
    progress_percentage = min(100, int((completed_ciphers / total_ciphers) * 100)) if total_ciphers > 0 else 0
    
    # Get recent activities
    recent_activities = UserActivity.query.filter_by(user_id=user_id)\
        .order_by(UserActivity.timestamp.desc())\
        .limit(5).all()
    
    # Get challenge stats
    challenge_attempts = ChallengeAttempt.query.filter_by(user_id=user_id).all()
    completed_challenges = sum(1 for attempt in challenge_attempts if attempt.completed)
    
    # Get achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user_id).count()
    
    return {
        'username': User.query.get(user_id).username,
        'user_level': progress.level,
        'user_xp': progress.xp,
        'completed_ciphers': completed_ciphers,
        'total_ciphers': total_ciphers,
        'progress_percentage': progress_percentage,
        'streak_days': progress.current_streak,
        'challenges_completed': completed_challenges,
        'total_challenges': 12,
        'achievements_unlocked': user_achievements,
        'total_achievements': 12,
        'encryptions_performed': progress.encryptions_performed,
        'learning_time': progress.learning_time_minutes,
        'recent_activities': recent_activities
    }

def get_cipher_progress_data(user_id):
    """Get detailed cipher progress data"""
    cipher_data = []
    
    # List of ciphers
    ciphers = [
        {'name': 'Caesar Cipher', 'code': 'caesar', 'year': '100 SM', 'free': True, 'difficulty': 'easy'},
        {'name': 'Vigenère Cipher', 'code': 'vigenere', 'year': '1553', 'free': True, 'difficulty': 'medium'},
        {'name': 'Substitution Cipher', 'code': 'substitution', 'year': '500 SM', 'free': False, 'difficulty': 'medium'},
        {'name': 'Playfair Cipher', 'code': 'playfair', 'year': '1854', 'free': False, 'difficulty': 'medium'},
        {'name': 'Hill Cipher', 'code': 'hill', 'year': '1929', 'free': False, 'difficulty': 'hard'},
        {'name': 'RSA Encryption', 'code': 'rsa', 'year': '1977', 'free': False, 'difficulty': 'hard'},
        {'name': 'AES Encryption', 'code': 'aes', 'year': '2001', 'free': False, 'difficulty': 'hard'},
        {'name': 'DES Encryption', 'code': 'des', 'year': '1977', 'free': False, 'difficulty': 'medium'},
        {'name': 'Blowfish', 'code': 'blowfish', 'year': '1993', 'free': False, 'difficulty': 'hard'},
        {'name': 'Transposition Cipher', 'code': 'transposition', 'year': '500 SM', 'free': False, 'difficulty': 'easy'},
        {'name': 'Rail Fence Cipher', 'code': 'railfence', 'year': '1861', 'free': False, 'difficulty': 'easy'},
        {'name': 'Columnar Transposition', 'code': 'columnar', 'year': '1914', 'free': False, 'difficulty': 'medium'},
        {'name': 'Route Cipher', 'code': 'route', 'year': '1918', 'free': False, 'difficulty': 'medium'},
    ]
    
    for cipher in ciphers:
        usage = CipherUsage.query.filter_by(
            user_id=user_id, 
            cipher_name=cipher['name']
        ).first()
        
        # Calculate completion percentage based on usage
        completion = 0
        if usage:
            if usage.usage_count >= 5:
                completion = 100
            elif usage.usage_count >= 3:
                completion = 75
            elif usage.usage_count >= 2:
                completion = 45
            elif usage.usage_count >= 1:
                completion = 20
        
        cipher_data.append({
            **cipher,
            'completion': completion,
            'used': usage is not None,
            'usage_count': usage.usage_count if usage else 0
        })
    
    return cipher_data

def update_user_xp(user_id, xp_earned, activity_type="quiz"):
    """Update user XP and check level up"""
    progress = get_user_progress(user_id)
    
    old_level = progress.level
    progress.xp += xp_earned
    
    new_level = (progress.xp // 100) + 1
    if new_level > old_level:
        progress.level = new_level
        activity = UserActivity(
            user_id=user_id,
            activity_type='level_up',
            description=f'Level up dari {old_level} ke {new_level}!',
            xp_gained=xp_earned
        )
        db.session.add(activity)
    
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        description=f'Mendapatkan {xp_earned} XP dari {activity_type}',
        xp_gained=xp_earned
    )
    db.session.add(activity)
    
    today = date.today()
    if progress.last_active_date != today:
        if (today - progress.last_active_date).days == 1:
            progress.current_streak += 1
        else:
            progress.current_streak = 1
        progress.last_active_date = today
    
    db.session.commit()
    return progress

def check_module_achievements(user_id):
    """Check and award achievements for module completion"""
    # Count completed modules
    completed_modules = UserModuleProgress.query.filter_by(
        user_id=user_id,
        completed=True
    ).count()
    
    # Achievement: Module Novice
    if completed_modules >= 1:
        award_achievement(user_id, 'module_novice')
    
    # Achievement: Module Explorer
    if completed_modules >= 5:
        award_achievement(user_id, 'module_explorer')
    
    # Achievement: Module Master
    if completed_modules >= 10:
        award_achievement(user_id, 'module_master')
    
    # Check for category completion achievements
    categories = db.session.query(LearningModule.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    for category in categories:
        modules_in_category = LearningModule.query.filter_by(category=category).count()
        completed_in_category = 0
        
        modules = LearningModule.query.filter_by(category=category).all()
        for module in modules:
            progress = UserModuleProgress.query.filter_by(
                user_id=user_id,
                module_id=module.id,
                completed=True
            ).first()
            if progress:
                completed_in_category += 1
        
        # Achievement: Complete a category
        if completed_in_category == modules_in_category and modules_in_category > 0:
            award_achievement(user_id, f'category_{category.lower().replace(" ", "_")}_completed')

def award_achievement(user_id, achievement_code):
    """Award an achievement to user"""
    achievement = Achievement.query.filter_by(requirement=achievement_code).first()
    
    if not achievement:
        return
    
    # Check if user already has this achievement
    existing = UserAchievement.query.filter_by(
        user_id=user_id,
        achievement_id=achievement.id
    ).first()
    
    if existing:
        return
    
    # Award achievement
    user_achievement = UserAchievement(
        user_id=user_id,
        achievement_id=achievement.id
    )
    db.session.add(user_achievement)
    
    # Give XP reward
    update_user_xp(user_id, achievement.xp_reward, 'achievement')
    
    # Log activity
    activity = UserActivity(
        user_id=user_id,
        activity_type='achievement_unlocked',
        description=f'Unlocked achievement: {achievement.name}',
        xp_gained=achievement.xp_reward
    )
    db.session.add(activity)

def log_cipher_usage(user_id, cipher_name):
    """Log cipher usage for statistics"""
    usage = CipherUsage.query.filter_by(user_id=user_id, cipher_name=cipher_name).first()
    if usage:
        usage.usage_count += 1
        usage.last_used = datetime.now()
    else:
        usage = CipherUsage(
            user_id=user_id,
            cipher_name=cipher_name,
            usage_count=1
        )
        db.session.add(usage)
    
    progress = get_user_progress(user_id)
    progress.encryptions_performed += 1
    db.session.commit()

def get_tutorial_data(tutorial_slug=None, category_slug=None):
    """Get tutorial data for tutorials page"""
    tutorials_data = []
    categories_data = []
    featured_tutorials = []
    
    # Get all categories
    categories = TutorialCategory.query.order_by(TutorialCategory.order).all()
    for category in categories:
        # Count tutorials in category
        tutorial_count = Tutorial.query.filter_by(category=category.name).count()
        
        # Calculate user progress for this category
        if current_user.is_authenticated:
            # Get user progress for tutorials in this category
            tutorials_in_category = Tutorial.query.filter_by(category=category.name).all()
            completed = 0
            total = len(tutorials_in_category)
            
            if total > 0:
                for tut in tutorials_in_category:
                    progress = UserTutorialProgress.query.filter_by(
                        user_id=current_user.id,
                        tutorial_id=tut.id
                    ).first()
                    if progress and progress.completed:
                        completed += 1
                
                progress_percentage = int((completed / total) * 100)
            else:
                progress_percentage = 0
        else:
            progress_percentage = 0
        
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'icon': category.icon,
            'color': category.color,
            'tutorial_count': tutorial_count,
            'is_premium': category.is_premium,
            'progress_percentage': progress_percentage,
            'completed': completed if current_user.is_authenticated else 0,
            'total': total
        })
    
    # Get featured tutorials
    featured = Tutorial.query.filter_by(featured=True).order_by(Tutorial.order).limit(6).all()
    for tutorial in featured:
        progress_data = get_tutorial_progress_data(tutorial.id) if current_user.is_authenticated else None
        
        tutorials_data.append({
            'id': tutorial.id,
            'title': tutorial.title,
            'slug': tutorial.slug,
            'description': tutorial.description,
            'difficulty': tutorial.difficulty,
            'duration': tutorial.duration_minutes,
            'category': tutorial.category,
            'tags': tutorial.tags.split(',') if tutorial.tags else [],
            'is_premium': tutorial.is_premium,
            'is_new': tutorial.is_new,
            'progress_percentage': progress_data['progress_percentage'] if progress_data else 0,
            'completed': progress_data['completed'] if progress_data else False
        })
    
    # Get specific tutorial if requested
    tutorial_detail = None
    if tutorial_slug:
        tutorial = Tutorial.query.filter_by(slug=tutorial_slug).first()
        if tutorial:
            progress_data = get_tutorial_progress_data(tutorial.id) if current_user.is_authenticated else None
            references = TutorialReference.query.filter_by(tutorial_id=tutorial.id).all()
            
            tutorial_detail = {
                'id': tutorial.id,
                'title': tutorial.title,
                'slug': tutorial.slug,
                'description': tutorial.description,
                'content': tutorial.content,
                'difficulty': tutorial.difficulty,
                'duration': tutorial.duration_minutes,
                'category': tutorial.category,
                'tags': tutorial.tags.split(',') if tutorial.tags else [],
                'is_premium': tutorial.is_premium,
                'is_new': tutorial.is_new,
                'estimated_reading_time': tutorial.estimated_reading_time,
                'created_at': tutorial.created_at,
                'progress_percentage': progress_data['progress_percentage'] if progress_data else 0,
                'completed': progress_data['completed'] if progress_data else False,
                'time_spent': progress_data['time_spent_minutes'] if progress_data else 0,
                'references': [{
                    'title': ref.title,
                    'url': ref.url,
                    'source': ref.source,
                    'icon': ref.icon,
                    'description': ref.description
                } for ref in references]
            }
    
    # Get category tutorials if requested
    category_tutorials = []
    if category_slug:
        category = TutorialCategory.query.filter_by(slug=category_slug).first()
        if category:
            tutorials_in_category = Tutorial.query.filter_by(category=category.name)\
                .order_by(Tutorial.order).all()
            
            for tutorial in tutorials_in_category:
                progress_data = get_tutorial_progress_data(tutorial.id) if current_user.is_authenticated else None
                
                category_tutorials.append({
                    'id': tutorial.id,
                    'title': tutorial.title,
                    'slug': tutorial.slug,
                    'description': tutorial.description,
                    'difficulty': tutorial.difficulty,
                    'duration': tutorial.duration_minutes,
                    'tags': tutorial.tags.split(',') if tutorial.tags else [],
                    'is_premium': tutorial.is_premium,
                    'is_new': tutorial.is_new,
                    'progress_percentage': progress_data['progress_percentage'] if progress_data else 0,
                    'completed': progress_data['completed'] if progress_data else False
                })
    
    return {
        'categories': categories_data,
        'tutorials': tutorials_data,
        'featured_count': len(featured),
        'total_tutorials': Tutorial.query.count(),
        'total_categories': len(categories),
        'user_progress_percentage': calculate_overall_tutorial_progress() if current_user.is_authenticated else 0,
        'tutorial_detail': tutorial_detail,
        'category_tutorials': category_tutorials,
        'category_name': category.name if category_slug else None
    }

def get_tutorial_progress_data(tutorial_id):
    """Get user progress for specific tutorial"""
    if not current_user.is_authenticated:
        return {
            'progress_percentage': 0,
            'completed': False,
            'time_spent_minutes': 0
        }
    
    progress = UserTutorialProgress.query.filter_by(
        user_id=current_user.id,
        tutorial_id=tutorial_id
    ).first()
    
    if progress:
        return {
            'progress_percentage': progress.progress_percentage,
            'completed': progress.completed,
            'time_spent_minutes': progress.time_spent_minutes,
            'started_at': progress.started_at,
            'last_accessed': progress.last_accessed
        }
    else:
        return {
            'progress_percentage': 0,
            'completed': False,
            'time_spent_minutes': 0
        }

def calculate_overall_tutorial_progress():
    """Calculate overall tutorial progress for user"""
    if not current_user.is_authenticated:
        return 0
    
    total_tutorials = Tutorial.query.count()
    if total_tutorials == 0:
        return 0
    
    completed_tutorials = UserTutorialProgress.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()
    
    return int((completed_tutorials / total_tutorials) * 100)

def update_tutorial_progress(tutorial_id, progress_percentage, time_spent_minutes=0):
    """Update user progress for tutorial"""
    if not current_user.is_authenticated:
        return False
    
    progress = UserTutorialProgress.query.filter_by(
        user_id=current_user.id,
        tutorial_id=tutorial_id
    ).first()
    
    if not progress:
        progress = UserTutorialProgress(
            user_id=current_user.id,
            tutorial_id=tutorial_id,
            progress_percentage=progress_percentage,
            time_spent_minutes=time_spent_minutes
        )
        db.session.add(progress)
    else:
        progress.progress_percentage = progress_percentage
        progress.time_spent_minutes += time_spent_minutes
        progress.last_accessed = datetime.utcnow()
        
        # Mark as completed if progress is 100%
        if progress_percentage >= 100 and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            
            # Give XP reward
            tutorial = Tutorial.query.get(tutorial_id)
            xp_earned = 100 if tutorial.difficulty == 'beginner' else 200 if tutorial.difficulty == 'intermediate' else 300
            update_user_xp(current_user.id, xp_earned, 'tutorial_completion')
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                activity_type='tutorial_completed',
                description=f'Completed tutorial: {tutorial.title}',
                xp_gained=xp_earned
            )
            db.session.add(activity)
    
    db.session.commit()
    return True

def search_tutorials(search_term, limit=20):
    """Search tutorials by title, description, or tags"""
    search_term = f"%{search_term}%"
    
    tutorials = Tutorial.query.filter(
        db.or_(
            Tutorial.title.ilike(search_term),
            Tutorial.description.ilike(search_term),
            Tutorial.tags.ilike(search_term),
            Tutorial.content.ilike(search_term)
        )
    ).limit(limit).all()
    
    results = []
    for tutorial in tutorials:
        progress_data = get_tutorial_progress_data(tutorial.id) if current_user.is_authenticated else None
        
        results.append({
            'id': tutorial.id,
            'title': tutorial.title,
            'slug': tutorial.slug,
            'description': tutorial.description,
            'difficulty': tutorial.difficulty,
            'category': tutorial.category,
            'is_premium': tutorial.is_premium,
            'progress_percentage': progress_data['progress_percentage'] if progress_data else 0
        })
    
    return results

def get_google_search_references(search_term):
    """Generate Google search references for a tutorial topic"""
    search_queries = [
        f"{search_term} cryptography tutorial",
        f"{search_term} algorithm explanation",
        f"{search_term} implementation Python",
        f"{search_term} Wikipedia",
        f"{search_term} computer science"
    ]
    
    references = []
    sources = [
        {'name': 'Wikipedia', 'icon': 'fab fa-wikipedia-w', 'color': '#4285F4'},
        {'name': 'YouTube', 'icon': 'fab fa-youtube', 'color': '#FF0000'},
        {'name': 'Khan Academy', 'icon': 'fas fa-graduation-cap', 'color': '#14B8A6'},
        {'name': 'GeeksforGeeks', 'icon': 'fas fa-code', 'color': '#0F9D58'},
        {'name': 'Stack Overflow', 'icon': 'fab fa-stack-overflow', 'color': '#F48024'},
        {'name': 'Google Scholar', 'icon': 'fas fa-graduation-cap', 'color': '#4285F4'}
    ]
    
    for i, query in enumerate(search_queries):
        if i < len(sources):
            source = sources[i]
            references.append({
                'title': f"Search: {query}",
                'url': f"https://www.google.com/search?q={urllib.parse.quote(query)}",
                'source': source['name'],
                'icon': source['icon'],
                'color': source['color'],
                'description': f"Find resources about {search_term} on {source['name']}"
            })
    
    return references

def get_chatbot_response(user_message):
    try:
        # Load response database
        with open('chatbot_responses.json', 'r', encoding='utf-8') as f:
            responses = json.load(f)
        
        # Simple keyword matching
        user_message_lower = user_message.lower()
        
        # Check for specific keywords
        for key, response in responses.items():
            keywords = key.split()
            matches = sum(1 for keyword in keywords if keyword in user_message_lower)
            
            # If at least 60% of keywords match
            if matches >= len(keywords) * 0.6:
                return response
        
        # Return default response if no match
        return responses.get('default', {
            'answer': 'Maaf, saya belum memahami pertanyaan Anda. Silakan tanyakan tentang kriptografi atau keamanan sistem.',
            'follow_up': ['konsep dasar kriptografi', 'algoritma rsa', 'fungsi hash'],
            'tags': ['help']
        })
    except Exception as e:
        print(f"Error loading chatbot responses: {e}")
        return {
            'answer': 'Maaf, sistem chatbot sedang mengalami masalah. Silakan coba lagi nanti.',
            'follow_up': [],
            'tags': ['error']
        }

# =============== MIDDLEWARE ===============
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# =============== ROUTES ===============
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/search')
@login_required
def search_page():
    """Halaman pencarian lengkap"""
    search_term = request.args.get('q', '').strip()
    
    if not search_term:
        return render_template('search.html', 
                             search_term='',
                             results={},
                             total=0)
    
    # Panggil API search yang sudah ada
    from flask import jsonify
    try:
        results = api_global_search()
        if isinstance(results, tuple):
            # Handle error response
            results_data = {'success': False, 'results': {}}
        else:
            results_data = results.get_json()
    except:
        results_data = {'success': False, 'results': {}}
    
    return render_template('search.html',
                         search_term=search_term,
                         results=results_data.get('results', {}) if results_data.get('success') else {},
                         total=results_data.get('total', 0))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Password tidak cocok!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        progress = UserProgress(user_id=new_user.id)
        db.session.add(progress)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"\n🔐 LOGIN PAGE ACCESSED")
    print(f"DEBUG - Current user before login: {current_user}")
    print(f"DEBUG - Is authenticated: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        print(f"DEBUG - User already logged in, redirecting to dashboard")
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"DEBUG - Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            print(f"DEBUG - Password valid for user: {user.id}")
            login_user(user, remember=True)
            session.permanent = True
            session['logout_token'] = secrets.token_urlsafe(32)
            session['user_id'] = user.id
            session['username'] = user.username
            
            # Update last login
            user.update_last_login()
            
            progress = get_user_progress(user.id)
            progress.learning_time_minutes += 1
            
            activity = UserActivity(
                user_id=user.id,
                activity_type='login',
                description='User login ke sistem'
            )
            db.session.add(activity)
            db.session.commit()
            
            print(f"DEBUG - Login successful for user: {user.id}")
            print(f"DEBUG - Session after login: {dict(session)}")
            
            # Handle AJAX request
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Login berhasil!',
                    'redirect': url_for('dashboard')
                })
            
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        else:
            print(f"DEBUG - Login failed for username: {username}")
            flash('Username atau password salah!', 'danger')
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@secure_logout_required
def logout():
    user_id = current_user.id
    logout_user()
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    print(f"\n🏠 DASHBOARD ACCESSED")
    print(f"DEBUG - Current user: {current_user}")
    print(f"DEBUG - User ID: {current_user.id}")
    print(f"DEBUG - Is authenticated: {current_user.is_authenticated}")
    print(f"DEBUG - Session: {dict(session)}")
    
    if 'logout_token' not in session:
        session['logout_token'] = secrets.token_urlsafe(32)
    
    progress = get_user_progress(current_user.id)
    cipher_usages = CipherUsage.query.filter_by(user_id=current_user.id).count()
    total_ciphers = 15
    
    return render_template('dashboard.html', 
                         logout_token=session['logout_token'],
                         user_level=progress.level,
                         user_xp=progress.xp,
                         completed_ciphers=cipher_usages,
                         total_ciphers=total_ciphers,
                         streak_days=progress.current_streak)


@app.route('/learn')
@login_required
def learn():
    """Halaman pusat pembelajaran"""
    
    # Get user learning data
    learn_data = get_learn_data(current_user.id)
    
    # Get learning modules
    modules = LearningModule.query.order_by(LearningModule.order).all()
    completed_modules = UserModuleProgress.query.filter_by(
        user_id=current_user.id, 
        completed=True
    ).count()
    
    # Get video courses
    videos = VideoCourse.query.all()
    watched_videos = UserVideoProgress.query.filter_by(
        user_id=current_user.id,
        watched=True
    ).count()
    
    # Get glossary terms
    terms = GlossaryTerm.query.all()
    
    return render_template(
        'learn.html',
        # Learning stats
        completed_modules=completed_modules,
        total_modules=len(modules),
        total_study_hours=learn_data['total_study_hours'],
        streak_days=learn_data['streak_days'],
        progress=learn_data['progress_percentage'],
        
        # Module stats
        module_count=len(modules),
        
        # Video stats
        video_count=len(videos),
        premium_videos=len([v for v in videos if v.is_premium]),
        video_hours=sum(v.duration for v in videos) // 60,
        
        # Glossary stats
        term_count=len(terms),
        categories=len(set([t.category for t in terms if t.category])),
        
        # General stats
        learning_count=learn_data['learning_count'],
        cipher_count=learn_data['cipher_count'],
        challenge_count=learn_data['challenge_count'],
        completed_ciphers=learn_data['completed_ciphers'],
        user_level=learn_data['user_level'],
        user_xp=learn_data['user_xp']
    )

@app.route('/ciphers')
@login_required
def ciphers():
    """Halaman daftar semua cipher"""
    return render_template('ciphers.html', 
                         progress_percentage=65,
                         completed_ciphers=3,
                         streak_days=7,
                         user_xp=1250)

@app.route('/achievements')
@login_required
def achievements():
    """Halaman pencapaian/pencapaian pengguna"""
    # Get user achievements
    user_achievements = UserAchievement.query.filter_by(
        user_id=current_user.id
    ).all()
    
    # Get all available achievements
    all_achievements = Achievement.query.all()
    
    # Calculate progress
    unlocked_count = len(user_achievements)
    total_count = len(all_achievements)
    progress_percentage = int((unlocked_count / total_count) * 100) if total_count > 0 else 0
    
    # Get recent unlocked achievements
    recent_achievements = UserAchievement.query.filter_by(
        user_id=current_user.id
    ).order_by(UserAchievement.unlocked_at.desc()).limit(5).all()
    
    return render_template('achievements.html',
                         user_achievements=user_achievements,
                         all_achievements=all_achievements,
                         unlocked_count=unlocked_count,
                         total_count=total_count,
                         progress_percentage=progress_percentage,
                         recent_achievements=recent_achievements)

@app.route('/forum')
@login_required
def forum():
    """Halaman forum utama"""
    # Note: Anda perlu membuat model ForumTopic dan ForumPost terlebih dahulu
    return render_template('forum/index.html')

@app.route('/certificates')
@login_required
def certificates():
    return render_template('certificates.html')

@app.route('/activity')
@login_required
def activity():
    """Halaman aktivitas pengguna"""
    return render_template('activity.html')

@app.route('/challenges')
@login_required
def challenges():
    return render_template('challenges.html')

@app.route('/challenges/alt')
@login_required
def challenges_alt():
    """Halaman tantangan alternatif"""
    return render_template('challenges_alt.html')

@app.route('/support')
def support():
    """Halaman support/help"""
    return render_template('support.html')

@app.route('/tanya_jawab')
def tanya_jawab():
    user_data = {
        'username': session.get('username', 'Pengguna'),
        'user_level': session.get('level', 1),
        'user_xp': session.get('xp', 0),
        'completed_ciphers': session.get('completed_ciphers', 0)
    }

    return render_template('tanya_jawab.html', **user_data)

@app.route('/profile')
@login_required
def profile():
    progress = get_user_progress(current_user.id)
    
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'full_name': current_user.username,
        'user_level': progress.level,
        'xp_points': progress.xp,
        'streak_days': progress.current_streak,
        'completed_ciphers': CipherUsage.query.filter_by(user_id=current_user.id).count(),
        'total_ciphers': 20,
        'is_premium': current_user.is_premium,
        'premium_expiry': current_user.premium_expires,
        'bio': current_user.bio or 'Penggemar kriptografi yang sedang belajar enkripsi modern.',
        'skills': ['Kriptografi Dasar', 'Enkripsi Caesar', 'Analisis Cipher'],
        'join_date': current_user.created_at.strftime('%B %Y') if current_user.created_at else 'Januari 2024'
    }
    return render_template('profile.html', **user_data)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.json
    return jsonify({'success': True, 'message': 'Profile updated'})

# =============== TUTORIAL ROUTES ===============
@app.route('/tutorials')
@login_required
def tutorials_page():
    """Halaman utama tutorial library"""
    # Dapatkan data tutorial
    tutorial_data = get_tutorial_data()
    
    # Hitung progress keseluruhan
    if current_user.is_authenticated:
        total_tutorials = Tutorial.query.count()
        completed_tutorials = UserTutorialProgress.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).count()
        overall_progress = int((completed_tutorials / total_tutorials) * 100) if total_tutorials > 0 else 0
    else:
        overall_progress = 0
    
    return render_template('tutorials.html',
                         categories=tutorial_data['categories'],
                         tutorials=tutorial_data['tutorials'],
                         featured_count=tutorial_data['featured_count'],
                         total_tutorials=tutorial_data['total_tutorials'],
                         total_categories=tutorial_data['total_categories'],
                         overall_progress=overall_progress)

@app.route('/tutorials/category/<string:category_slug>')
@login_required
def tutorial_category(category_slug):
    """Halaman tutorial berdasarkan kategori"""
    tutorial_data = get_tutorial_data(category_slug=category_slug)
    
    if not tutorial_data['category_tutorials']:
        flash('Kategori tidak ditemukan', 'warning')
        return redirect(url_for('tutorials_page'))
    
    return render_template('tutorials_category.html',
                         category_name=tutorial_data['category_name'],
                         tutorials=tutorial_data['category_tutorials'],
                         categories=tutorial_data['categories'])

@app.route('/tutorials/<string:tutorial_slug>')
@login_required
def tutorial_detail(tutorial_slug):
    """Halaman detail tutorial"""
    tutorial_data = get_tutorial_data(tutorial_slug=tutorial_slug)
    
    if not tutorial_data['tutorial_detail']:
        flash('Tutorial tidak ditemukan', 'danger')
        return redirect(url_for('tutorials_page'))
    
    # Cek apakah tutorial premium
    tutorial = tutorial_data['tutorial_detail']
    if tutorial['is_premium'] and not current_user.is_premium:
        flash('Tutorial ini memerlukan akun premium', 'warning')
        return redirect(url_for('premium'))
    
    # Update view count
    tut = Tutorial.query.filter_by(slug=tutorial_slug).first()
    if tut:
        tut.views += 1
        db.session.commit()
    
    # Update user progress
    update_tutorial_progress(tut.id, 10, 5)  # 10% progress, 5 minutes spent
    
    return render_template('tutorial_detail.html',
                         tutorial=tutorial_data['tutorial_detail'],
                         categories=tutorial_data['categories'])


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/premium')
def premium():
    return render_template('premium.html')

@app.route('/premium/upgrade', methods=['POST'])
@login_required
def upgrade_premium():
    """Handle premium upgrade payment"""
    
    # Get selected plan from form
    plan = request.form.get('plan')
    
    # Validate plan
    valid_plans = ['monthly', 'yearly', 'lifetime']
    if plan not in valid_plans:
        flash('Pilih paket yang valid', 'error')
        return redirect(url_for('premium'))
    
    # For demo purposes, just upgrade user
    current_user.is_premium = True
    
    # Set expiration based on plan
    if plan == 'monthly':
        expires = datetime.utcnow() + timedelta(days=30)
    elif plan == 'yearly':
        expires = datetime.utcnow() + timedelta(days=365)
    else:  # lifetime
        expires = datetime.utcnow() + timedelta(days=365*10)  # 10 years
    
    current_user.premium_expires = expires
    
    # Beri bonus XP untuk upgrading
    progress = get_user_progress(current_user.id)
    if progress:
        progress.xp += 500
        db.session.commit()
    
    # Log the upgrade
    activity = UserActivity(
        user_id=current_user.id,
        activity_type='premium_upgrade',
        description=f'Upgraded to {plan} premium plan',
        xp_gained=500
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('🎉 Upgrade berhasil! Selamat menikmati fitur premium!', 'success')
    return redirect(url_for('dashboard'))

# =============== PASSWORD RESET ROUTES ===============
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Halaman lupa password"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Harap masukkan alamat email', 'danger')
            return redirect(url_for('forgot_password'))
        
        # Cari user berdasarkan email
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Generate reset token (simpan di database atau session)
                reset_token = secrets.token_urlsafe(32)
                
                # Simpan token di session dengan expiry time (1 jam)
                session['reset_token'] = reset_token
                session['reset_user_id'] = user.id
                session['reset_expiry'] = datetime.now().timestamp() + 3600  # 1 jam
                
                # Log aktivitas
                activity = UserActivity(
                    user_id=user.id,
                    activity_type='password_reset_request',
                    description='Mengirim permintaan reset password',
                    xp_gained=0
                )
                db.session.add(activity)
                db.session.commit()
                
                # Untuk demo, kita tampilkan token di console
                print(f"RESET TOKEN untuk {email}: {reset_token}")
                
                # In production, you would send an email here:
                # send_reset_email(email, reset_token)
                
                flash('Link reset password telah dikirim ke email Anda!', 'success')
                return render_template('forgot_password.html', success=True, email=email)
                
            except Exception as e:
                print(f"Error: {e}")
                flash('Terjadi kesalahan saat mengirim email reset. Silakan coba lagi.', 'danger')
        else:
            # Untuk keamanan, tetap tampilkan pesan sukses meski email tidak ditemukan
            flash('Jika email terdaftar, link reset akan dikirim.', 'info')
            return render_template('forgot_password.html', success=True)
    
    return render_template('forgot_password.html', success=False)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Halaman reset password dengan token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Verifikasi token dari session
    stored_token = session.get('reset_token')
    user_id = session.get('reset_user_id')
    expiry_time = session.get('reset_expiry')
    
    if (not stored_token or not user_id or not expiry_time or 
        stored_token != token or 
        datetime.now().timestamp() > expiry_time):
        flash('Token reset password tidak valid atau telah kadaluarsa.', 'danger')
        return redirect(url_for('forgot_password'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Harap isi semua field.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        if password != confirm_password:
            flash('Password tidak cocok.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        if len(password) < 6:
            flash('Password minimal 6 karakter.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        try:
            # Update password
            user.set_password(password)
            
            # Hapus token dari session
            session.pop('reset_token', None)
            session.pop('reset_user_id', None)
            session.pop('reset_expiry', None)
            
            # Log aktivitas
            activity = UserActivity(
                user_id=user.id,
                activity_type='password_reset',
                description='Password berhasil direset',
                xp_gained=0
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('Password berhasil direset! Silakan login dengan password baru.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Error resetting password: {e}")
            flash('Terjadi kesalahan saat reset password. Silakan coba lagi.', 'danger')
    
    return render_template('reset_password.html', token=token, email=user.email)

# =============== CIPHER PAGES ===============
@app.route('/caesar')
def caesar():
    return render_template('caesar.html')

@app.route('/vigenere')
def vigenere():
    return render_template('vigenere.html')

@app.route('/bruteforce')
def bruteforce():
    return render_template('bruteforce.html')

# Fitur Premium (Login Required)
@app.route('/substitution')
@login_required
def substitution():
    return render_template('substitution.html')

@app.route('/transposition')
@login_required
def transposition():
    return render_template('transposition.html')

@app.route('/playfair')
@login_required
def playfair():
    return render_template('playfair.html')

@app.route('/hill')
@login_required
def hill():
    return render_template('hill.html')

@app.route('/rsa')
@login_required
def rsa():
    return render_template('rsa.html')

@app.route('/hash')
@login_required
def hash_func():
    return render_template('hash.html')

# FITUR PREMIUM BARU - Modern Encryption
@app.route('/aes')
@login_required
def aes_page():
    return render_template('aes.html')

@app.route('/des')
@login_required
def des_page():
    return render_template('des.html')

@app.route('/triple-des')
@login_required
def triple_des_page():
    return render_template('triple_des.html')

@app.route('/blowfish')
@login_required
def blowfish_page():
    return render_template('blowfish.html')

# =============== LEARNING PAGES ===============
@app.route('/learn/modules')  
@login_required
def modules():
    """Halaman modul pembelajaran"""
    # Get all learning modules with user progress
    modules = LearningModule.query.order_by(LearningModule.order).all()
    
    # Get categories
    categories = db.session.query(LearningModule.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    # Calculate statistics
    total_modules = len(modules)
    completed_modules = UserModuleProgress.query.filter_by(
        user_id=current_user.id, 
        completed=True
    ).count() if current_user.is_authenticated else 0
    
    # Calculate progress by category
    category_stats = []
    for category in categories:
        modules_in_category = [m for m in modules if m.category == category]
        completed_in_category = 0
        
        if current_user.is_authenticated:
            for module in modules_in_category:
                progress = UserModuleProgress.query.filter_by(
                    user_id=current_user.id,
                    module_id=module.id
                ).first()
                if progress and progress.completed:
                    completed_in_category += 1
        
        category_stats.append({
            'name': category,
            'total': len(modules_in_category),
            'completed': completed_in_category,
            'progress_percentage': int((completed_in_category / len(modules_in_category)) * 100) if modules_in_category else 0
        })
    
    # Get user's module progress
    user_modules_data = []
    for module in modules:
        progress = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            module_id=module.id
        ).first() if current_user.is_authenticated else None
        
        # Get category index for color coding
        category_index = categories.index(module.category) if module.category in categories else 0
        category_color_class = f'category-icon-{category_index % 6 + 1}' if module.category else 'category-icon-1'
        
        user_modules_data.append({
            'id': module.id,
            'title': module.title,
            'description': module.description,
            'category': module.category,
            'difficulty': module.difficulty,
            'estimated_time': module.estimated_time,
            'is_premium': module.is_premium,
            'order': module.order,
            'created_at': module.created_at,
            'progress_percentage': progress.progress_percentage if progress else 0,
            'completed': progress.completed if progress else False,
            'time_spent': progress.time_spent if progress else 0,
            'started_at': progress.started_at if progress else None,
            'category_color_class': category_color_class
        })
    
    # Sort modules by order
    user_modules_data.sort(key=lambda x: x['order'])
    
    # Get overall progress
    overall_progress = int((completed_modules / total_modules) * 100) if total_modules > 0 else 0
    
    # Get recent activity
    recent_activities = UserActivity.query.filter_by(
        user_id=current_user.id,
        activity_type='learning'
    ).order_by(UserActivity.timestamp.desc()).limit(5).all() if current_user.is_authenticated else []
    
    return render_template('/learn/modules.html',
                         modules=user_modules_data,
                         categories=category_stats,
                         total_modules=total_modules,
                         completed_modules=completed_modules,
                         overall_progress=overall_progress,
                         recent_activities=recent_activities,
                         user_level=get_user_progress(current_user.id).level if current_user.is_authenticated else 1,
                         user_xp=get_user_progress(current_user.id).xp if current_user.is_authenticated else 0)

@app.route('/learn/glossary')
def glossary():
    return render_template('/learn/glossary.html')

@app.route('/learn/videos')
def video_courses():
    return render_template('/learn/videos.html')

@app.route('/learning-path')
def learning_path():
    return render_template('learning-path.html')

# =============== API ENDPOINTS ===============
@app.route('/api/weather', methods=['GET'])
@login_required
def api_get_weather():
    """API untuk mendapatkan data cuaca"""
    try:
        # Untuk demo, kita gunakan data static atau API external
        # Di production, bisa integrasi dengan OpenWeatherMap, dll.
        
        # Simulate random weather for demo
        import random
        temperatures = [28, 29, 30, 31, 32, 27, 26, 25]
        conditions = [
            {'icon': 'fa-cloud-sun', 'desc': 'Cerah Berawan'},
            {'icon': 'fa-sun', 'desc': 'Cerah'},
            {'icon': 'fa-cloud', 'desc': 'Berawan'},
            {'icon': 'fa-cloud-rain', 'desc': 'Hujan Ringan'},
            {'icon': 'fa-bolt', 'desc': 'Badai Petir'}
        ]
        
        # Untuk konsistensi, gunakan waktu sebagai seed
        current_hour = datetime.now().hour
        random.seed(current_hour)
        
        temp = random.choice(temperatures)
        condition = random.choice(conditions)
        
        return jsonify({
            'success': True,
            'temperature': temp,
            'condition': condition['desc'],
            'icon': condition['icon'],
            'location': 'Jakarta',
            'updated_at': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        # Fallback data
        return jsonify({
            'success': True,
            'temperature': 28,
            'condition': 'Cerah Berawan',
            'icon': 'fa-cloud-sun',
            'location': 'Jakarta',
            'updated_at': datetime.now().strftime('%H:%M'),
            'note': 'Data demo'
        })
    
@app.route('/api/search/global', methods=['POST'])
@login_required
def api_global_search():
    """API untuk pencarian global"""
    try:
        data = request.json
        search_term = data.get('search', '').strip()
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Masukkan kata kunci pencarian'
            }), 400
        
        results = {
            'ciphers': [],
            'modules': [],
            'challenges': [],
            'glossary': [],
            'videos': []
        }
        
        # 1. Cari cipher
        cipher_names = [
            'Caesar', 'Vigenère', 'Substitution', 'Playfair', 'Hill',
            'RSA', 'AES', 'DES', 'Blowfish', 'Transposition',
            'Rail Fence', 'Columnar Transposition', 'Route Cipher'
        ]
        
        for cipher in cipher_names:
            if search_term.lower() in cipher.lower():
                results['ciphers'].append({
                    'name': cipher,
                    'type': 'cipher',
                    'url': url_for(f'{cipher.lower().replace(" ", "_").replace("è", "e")}_page' if cipher in ['RSA', 'AES', 'DES'] else cipher.lower().replace(" ", "_").replace("è", "e"))
                })
        
        # 2. Cari modul pembelajaran
        modules = LearningModule.query.filter(
            db.or_(
                LearningModule.title.ilike(f'%{search_term}%'),
                LearningModule.description.ilike(f'%{search_term}%'),
                LearningModule.category.ilike(f'%{search_term}%')
            )
        ).limit(5).all()
        
        for module in modules:
            results['modules'].append({
                'name': module.title,
                'type': 'module',
                'category': module.category,
                'url': url_for('modules')
            })
        
        # 3. Cari tantangan
        challenges = Challenge.query.filter(
            db.or_(
                Challenge.title.ilike(f'%{search_term}%'),
                Challenge.cipher_name.ilike(f'%{search_term}%'),
                Challenge.description.ilike(f'%{search_term}%')
            )
        ).limit(5).all()
        
        for challenge in challenges:
            results['challenges'].append({
                'name': challenge.title,
                'type': 'challenge',
                'cipher': challenge.cipher_name,
                'url': url_for('challenges')
            })
        
        # 4. Cari istilah glossary
        glossary_terms = GlossaryTerm.query.filter(
            db.or_(
                GlossaryTerm.term.ilike(f'%{search_term}%'),
                GlossaryTerm.definition.ilike(f'%{search_term}%'),
                GlossaryTerm.category.ilike(f'%{search_term}%')
            )
        ).limit(5).all()
        
        for term in glossary_terms:
            results['glossary'].append({
                'name': term.term,
                'type': 'glossary',
                'category': term.category,
                'url': url_for('glossary')
            })
        
        # 5. Cari video
        videos = VideoCourse.query.filter(
            db.or_(
                VideoCourse.title.ilike(f'%{search_term}%'),
                VideoCourse.description.ilike(f'%{search_term}%'),
                VideoCourse.category.ilike(f'%{search_term}%'),
                VideoCourse.instructor.ilike(f'%{search_term}%')
            )
        ).limit(5).all()
        
        for video in videos:
            results['videos'].append({
                'name': video.title,
                'type': 'video',
                'instructor': video.instructor,
                'url': url_for('video_courses')
            })
        
        total_results = (
            len(results['ciphers']) + 
            len(results['modules']) + 
            len(results['challenges']) + 
            len(results['glossary']) + 
            len(results['videos'])
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'total': total_results,
            'search_term': search_term
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    """API untuk mendapatkan notifikasi user"""
    try:
        notifications = get_user_notifications(current_user.id, limit=20)
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type,
                'is_read': notif.is_read,
                'link': notif.link,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
                'time_ago': get_time_ago(notif.created_at)
            })
        
        unread_count = get_unread_notifications_count(current_user.id)
        
        return jsonify({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count,
            'total': len(notifications_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def api_mark_notification_read():
    """API untuk menandai notifikasi sebagai dibaca"""
    try:
        data = request.json
        notification_id = data.get('notification_id')
        
        if notification_id == 'all':
            # Tandai semua sebagai dibaca
            notifications = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).all()
            
            for notif in notifications:
                notif.is_read = True
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Semua notifikasi ditandai sebagai dibaca'
            })
        else:
            # Tandai satu notifikasi
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=current_user.id
            ).first()
            
            if not notification:
                return jsonify({
                    'success': False,
                    'error': 'Notifikasi tidak ditemukan'
                }), 404
            
            notification.is_read = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notifikasi ditandai sebagai dibaca'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/clear', methods=['POST'])
@login_required
def api_clear_notifications():
    """API untuk menghapus notifikasi yang sudah dibaca"""
    try:
        # Hapus notifikasi yang sudah dibaca dan sudah expired
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=True
        ).filter(
            Notification.expires_at.is_(None) | (Notification.expires_at < datetime.utcnow())
        ).all()
        
        count = len(notifications)
        
        for notif in notifications:
            db.session.delete(notif)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{count} notifikasi dihapus',
            'count': count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
@app.route('/api/modules', methods=['GET'])
@login_required
def api_get_modules():
    """API untuk mendapatkan semua modul"""
    try:
        modules = LearningModule.query.order_by(LearningModule.order).all()
        
        modules_data = []
        for module in modules:
            progress = UserModuleProgress.query.filter_by(
                user_id=current_user.id,
                module_id=module.id
            ).first()
            
            modules_data.append({
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'content': module.content,
                'difficulty': module.difficulty,
                'estimated_time': module.estimated_time,
                'category': module.category,
                'is_premium': module.is_premium,
                'order': module.order,
                'created_at': module.created_at.strftime('%Y-%m-%d') if module.created_at else None,
                'completed': progress.completed if progress else False,
                'progress_percentage': progress.progress_percentage if progress else 0,
                'time_spent': progress.time_spent if progress else 0
            })
        
        return jsonify({
            'success': True,
            'modules': modules_data,
            'total': len(modules_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/<int:module_id>', methods=['GET'])
@login_required
def api_get_module_detail(module_id):
    """API untuk mendapatkan detail modul"""
    try:
        module = LearningModule.query.get(module_id)
        
        if not module:
            return jsonify({
                'success': False,
                'error': 'Module not found'
            }), 404
        
        progress = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            module_id=module_id
        ).first()
        
        # Check if user has access (for premium modules)
        if module.is_premium and not current_user.is_premium:
            return jsonify({
                'success': False,
                'error': 'Premium module requires premium subscription',
                'requires_premium': True
            }), 403
        
        module_data = {
            'id': module.id,
            'title': module.title,
            'description': module.description,
            'content': module.content,
            'difficulty': module.difficulty,
            'estimated_time': module.estimated_time,
            'category': module.category,
            'is_premium': module.is_premium,
            'created_at': module.created_at.strftime('%Y-%m-%d') if module.created_at else None,
            'completed': progress.completed if progress else False,
            'progress_percentage': progress.progress_percentage if progress else 0,
            'time_spent': progress.time_spent if progress else 0,
            'started_at': progress.started_at.strftime('%Y-%m-%d %H:%M') if progress and progress.started_at else None,
            'completed_at': progress.completed_at.strftime('%Y-%m-%d %H:%M') if progress and progress.completed_at else None
        }
        
        return jsonify({
            'success': True,
            'module': module_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/<int:module_id>/start', methods=['POST'])
@login_required
def api_start_module(module_id):
    """API untuk memulai modul"""
    try:
        module = LearningModule.query.get(module_id)
        
        if not module:
            return jsonify({
                'success': False,
                'error': 'Module not found'
            }), 404
        
        # Check premium access
        if module.is_premium and not current_user.is_premium:
            return jsonify({
                'success': False,
                'error': 'Premium module requires premium subscription',
                'requires_premium': True
            }), 403
        
        # Create or update progress
        progress = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            module_id=module_id
        ).first()
        
        if not progress:
            progress = UserModuleProgress(
                user_id=current_user.id,
                module_id=module_id,
                progress_percentage=0,
                started_at=datetime.utcnow()
            )
            db.session.add(progress)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                activity_type='module_started',
                description=f'Started module: {module.title}',
                xp_gained=10
            )
            db.session.add(activity)
        
        progress.last_accessed = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Module started',
            'progress': progress.progress_percentage,
            'module_id': module_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/<int:module_id>/progress', methods=['POST'])
@login_required
def api_update_module_progress(module_id):
    """API untuk update progress modul"""
    try:
        data = request.json
        progress_percentage = data.get('progress', 0)
        time_spent = data.get('time_spent', 0)  # in minutes
        
        module = LearningModule.query.get(module_id)
        
        if not module:
            return jsonify({
                'success': False,
                'error': 'Module not found'
            }), 404
        
        # Get or create progress
        progress = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            module_id=module_id
        ).first()
        
        if not progress:
            progress = UserModuleProgress(
                user_id=current_user.id,
                module_id=module_id,
                progress_percentage=progress_percentage,
                time_spent=time_spent,
                started_at=datetime.utcnow()
            )
            db.session.add(progress)
        else:
            progress.progress_percentage = progress_percentage
            progress.time_spent += time_spent
            progress.last_accessed = datetime.utcnow()
            
            # Mark as completed if progress is 100%
            if progress_percentage >= 100 and not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.utcnow()
                
                # Give XP reward based on difficulty
                xp_earned = 100 if module.difficulty == 'beginner' else 200 if module.difficulty == 'intermediate' else 300
                update_user_xp(current_user.id, xp_earned, 'module_completion')
                
                # Log activity
                activity = UserActivity(
                    user_id=current_user.id,
                    activity_type='module_completed',
                    description=f'Completed module: {module.title}',
                    xp_gained=xp_earned
                )
                db.session.add(activity)
                
                # Check for module completion achievements
                check_module_achievements(current_user.id)
        
        # Update total learning time in user progress
        user_progress = get_user_progress(current_user.id)
        user_progress.learning_time_minutes += time_spent
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated',
            'progress': progress.progress_percentage,
            'completed': progress.completed,
            'time_spent': progress.time_spent,
            'xp_earned': xp_earned if progress.completed else 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/<int:module_id>/complete', methods=['POST'])
@login_required
def api_complete_module(module_id):
    """API untuk menyelesaikan modul"""
    try:
        module = LearningModule.query.get(module_id)
        
        if not module:
            return jsonify({
                'success': False,
                'error': 'Module not found'
            }), 404
        
        # Get or create progress
        progress = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            module_id=module_id
        ).first()
        
        if not progress:
            progress = UserModuleProgress(
                user_id=current_user.id,
                module_id=module_id,
                progress_percentage=100,
                completed=True,
                completed_at=datetime.utcnow(),
                started_at=datetime.utcnow()
            )
            db.session.add(progress)
        else:
            progress.progress_percentage = 100
            progress.completed = True
            progress.completed_at = datetime.utcnow()
        
        # Give XP reward
        xp_earned = 100 if module.difficulty == 'beginner' else 200 if module.difficulty == 'intermediate' else 300
        update_user_xp(current_user.id, xp_earned, 'module_completion')
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            activity_type='module_completed',
            description=f'Completed module: {module.title}',
            xp_gained=xp_earned
        )
        db.session.add(activity)
        
        # Update learning time
        user_progress = get_user_progress(current_user.id)
        estimated_time = module.estimated_time or 30
        user_progress.learning_time_minutes += estimated_time
        
        # Check for achievements
        check_module_achievements(current_user.id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Module completed',
            'xp_earned': xp_earned,
            'module_id': module_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/<int:module_id>/bookmark', methods=['POST'])
@login_required
def api_bookmark_module(module_id):
    """API untuk bookmark/unbookmark modul"""
    try:
        module = LearningModule.query.get(module_id)
        
        if not module:
            return jsonify({
                'success': False,
                'error': 'Module not found'
            }), 404
        
        # For now, we'll use UserActivity to track bookmarks
        # You can create a separate Bookmark model if needed
        
        activity = UserActivity(
            user_id=current_user.id,
            activity_type='module_bookmarked',
            description=f'Bookmarked module: {module.title}',
            xp_gained=5
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Module bookmarked'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/search', methods=['POST'])
@login_required
def api_search_modules():
    """API untuk mencari modul"""
    try:
        data = request.json
        search_term = data.get('search', '').strip()
        category = data.get('category', '')
        difficulty = data.get('difficulty', '')
        
        query = LearningModule.query
        
        if search_term:
            search_term = f"%{search_term}%"
            query = query.filter(
                db.or_(
                    LearningModule.title.ilike(search_term),
                    LearningModule.description.ilike(search_term),
                    LearningModule.content.ilike(search_term)
                )
            )
        
        if category:
            query = query.filter_by(category=category)
        
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        
        modules = query.order_by(LearningModule.order).all()
        
        modules_data = []
        for module in modules:
            progress = UserModuleProgress.query.filter_by(
                user_id=current_user.id,
                module_id=module.id
            ).first()
            
            modules_data.append({
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'difficulty': module.difficulty,
                'estimated_time': module.estimated_time,
                'category': module.category,
                'is_premium': module.is_premium,
                'progress_percentage': progress.progress_percentage if progress else 0,
                'completed': progress.completed if progress else False
            })
        
        return jsonify({
            'success': True,
            'modules': modules_data,
            'count': len(modules_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules/stats', methods=['GET'])
@login_required
def api_module_stats():
    """API untuk mendapatkan statistik modul"""
    try:
        total_modules = LearningModule.query.count()
        completed_modules = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).count()
        
        # Time spent learning
        total_time = db.session.query(db.func.sum(UserModuleProgress.time_spent_minutes))\
            .filter_by(user_id=current_user.id)\
            .scalar() or 0
        
        # Progress by category
        categories = db.session.query(LearningModule.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        category_stats = []
        for category in categories:
            modules_in_category = LearningModule.query.filter_by(category=category).count()
            completed_in_category = 0
            
            modules = LearningModule.query.filter_by(category=category).all()
            for module in modules:
                progress = UserModuleProgress.query.filter_by(
                    user_id=current_user.id,
                    module_id=module.id,
                    completed=True
                ).first()
                if progress:
                    completed_in_category += 1
            
            category_stats.append({
                'category': category,
                'total': modules_in_category,
                'completed': completed_in_category,
                'progress': int((completed_in_category / modules_in_category) * 100) if modules_in_category > 0 else 0
            })
        
        # Recent activity
        recent_activities = UserActivity.query.filter_by(
            user_id=current_user.id
        ).filter(
            UserActivity.activity_type.in_(['module_started', 'module_completed'])
        ).order_by(UserActivity.timestamp.desc()).limit(5).all()
        
        recent = []
        for act in recent_activities:
            recent.append({
                'type': act.activity_type,
                'description': act.description,
                'timestamp': act.timestamp.strftime('%Y-%m-%d %H:%M'),
                'xp_gained': act.xp_gained
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total_modules': total_modules,
                'completed_modules': completed_modules,
                'completion_percentage': int((completed_modules / total_modules) * 100) if total_modules > 0 else 0,
                'total_time_minutes': total_time,
                'total_time_hours': round(total_time / 60, 1),
                'category_stats': category_stats,
                'recent_activity': recent
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
@app.route('/api/caesar', methods=['POST'])
def api_caesar():
    data = request.get_json()
    text = data.get('text', '')
    shift = int(data.get('shift', 3))
    mode = data.get('mode', 'encrypt')
    
    if mode == 'encrypt':
        result = caesar_encrypt(text, shift)
    else:
        result = caesar_decrypt(text, shift)
    
    return jsonify({'result': result})

@app.route('/api/vigenere', methods=['POST'])
def api_vigenere():
    data = request.get_json()
    text = data.get('text', '')
    key = data.get('key', '')
    mode = data.get('mode', 'encrypt')
    
    if mode == 'encrypt':
        result = vigenere_encrypt(text, key)
    else:
        result = vigenere_decrypt(text, key)
    
    return jsonify({'result': result})

@app.route('/api/bruteforce', methods=['POST'])
def api_bruteforce():
    data = request.get_json()
    text = data.get('text', '')
    
    results = bruteforce_caesar(text)
    
    return jsonify({'results': results})

# API Endpoints - Premium (Login Required)
@app.route('/api/substitution', methods=['POST'])
@login_required
def api_substitution():
    data = request.get_json()
    text = data.get('text', '')
    keyword = data.get('keyword', '')
    mode = data.get('mode', 'encrypt')
    
    try:
        if mode == 'encrypt':
            key = generate_substitution_key(keyword) if keyword else generate_substitution_key()
            result = substitution_encrypt(text, key)
            return jsonify({'result': result, 'key': key})
        else:
            key = data.get('key', '')
            if not key or len(key) != 26:
                return jsonify({'error': 'Kunci harus 26 karakter A-Z'}), 400
            result = substitution_decrypt(text, key)
            return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/transposition/railfence', methods=['POST'])
@login_required
def api_railfence():
    data = request.get_json()
    text = data.get('text', '')
    rails = int(data.get('rails', 3))
    mode = data.get('mode', 'encrypt')
    
    if mode == 'encrypt':
        # Simple rail fence encryption
        fence = [''] * rails
        rail = 0
        direction = 1
        
        for char in text:
            fence[rail] += char
            rail += direction
            if rail == rails - 1 or rail == 0:
                direction = -direction
        
        result = ''.join(fence)
        return jsonify({'result': result})
    else:
        # Simple rail fence decryption
        try:
            result = rail_fence_decrypt(text, rails)
            return jsonify({'result': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/transposition/columnar', methods=['POST'])
@login_required
def api_columnar():
    data = request.get_json()
    text = data.get('text', '')
    key = data.get('key', '')
    mode = data.get('mode', 'encrypt')
    
    try:
        if mode == 'encrypt':
            result = columnar_transposition_encrypt(text, key)
            return jsonify({'result': result})
        else:
            result = columnar_transposition_decrypt(text, key)
            return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/transposition/route', methods=['POST'])
@login_required
def api_route():
    data = request.get_json()
    text = data.get('text', '')
    rows = int(data.get('rows', 3))
    cols = int(data.get('cols', 4))
    pattern = data.get('pattern', 'column')
    mode = data.get('mode', 'encrypt')
    
    try:
        if mode == 'encrypt':
            result = route_cipher_encrypt(text, rows, cols, pattern)
            return jsonify({'result': result})
        else:
            result = route_cipher_decrypt(text, rows, cols, pattern)
            return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/playfair', methods=['POST'])
@login_required
def api_playfair():
    data = request.get_json()
    text = data.get('text', '')
    key = data.get('key', '')
    mode = data.get('mode', 'encrypt')
    show_matrix = data.get('show_matrix', False)
    
    try:
        if mode == 'encrypt':
            result = playfair_encrypt(text, key)
            response = {'result': result}
            if show_matrix:
                matrix_info = analyze_playfair_key(key)
                response['matrix'] = matrix_info['matrix']
            return jsonify(response)
        else:
            result = playfair_decrypt(text, key)
            return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/playfair/matrix', methods=['POST'])
@login_required
def api_playfair_matrix():
    data = request.get_json()
    key = data.get('key', '')
    
    matrix_info = analyze_playfair_key(key)
    
    return jsonify({'matrix': matrix_info['matrix']})

@app.route('/api/hill', methods=['POST'])
@login_required
def api_hill():
    data = request.get_json()
    text = data.get('text', '')
    key_matrix_data = data.get('key_matrix', [])
    mode = data.get('mode', 'encrypt')
    
    try:
        key_matrix = key_matrix_data
        valid, message = validate_hill_key(key_matrix)
        if not valid:
            return jsonify({'error': message}), 400
        
        if mode == 'encrypt':
            result = hill_encrypt(text, key_matrix)
            return jsonify({'result': result})
        else:
            result = hill_decrypt(text, key_matrix)
            return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Hash API - Bcrypt & Argon2
@app.route('/api/hash/generate', methods=['POST'])
@login_required
def api_hash_generate():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'Text harus diisi'}), 400
    
    import hashlib
    
    hashes = {
        'md5': hashlib.md5(text.encode()).hexdigest(),
        'sha1': hashlib.sha1(text.encode()).hexdigest(),
        'sha256': hashlib.sha256(text.encode()).hexdigest(),
        'sha512': hashlib.sha512(text.encode()).hexdigest()
    }
    
    return jsonify({'hashes': hashes})

@app.route('/api/hash/bcrypt', methods=['POST'])
@login_required
def api_bcrypt_hash():
    data = request.get_json()
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password harus diisi'}), 400
    
    # Hash dengan bcrypt
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return jsonify({
        'algorithm': 'bcrypt',
        'hash': hashed.decode('utf-8'),
        'rounds': 12,
        'info': 'Bcrypt menggunakan cost factor (rounds) untuk mengatur kompleksitas'
    })

@app.route('/api/hash/argon2', methods=['POST'])
@login_required
def api_argon2_hash():
    data = request.get_json()
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password harus diisi'}), 400
    
    # Hash dengan argon2 dan tampilkan parameter
    hashed = ph.hash(password)
    
    return jsonify({
        'algorithm': 'argon2id',
        'hash': hashed,
        'parameters': {
            'time_cost': ph.time_cost,
            'memory_cost': f'{ph.memory_cost} KB ({ph.memory_cost/1024:.1f} MB)',
            'parallelism': ph.parallelism,
            'hash_length': ph.hash_len,
            'salt_length': ph.salt_len
        },
        'info': 'Argon2 adalah pemenang Password Hashing Competition (2015)'
    })

@app.route('/api/hash/compare-algos', methods=['POST'])
@login_required
def api_hash_compare_algos():
    data = request.get_json()
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password harus diisi'}), 400
    
    import time
    
    # Test Bcrypt
    start = time.time()
    bcrypt_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    bcrypt_time = time.time() - start
    
    # Test Argon2
    start = time.time()
    argon2_hash = ph.hash(password)
    argon2_time = time.time() - start
    
    return jsonify({
        'bcrypt': {
            'hash': bcrypt_hash.decode('utf-8'),
            'time': f'{bcrypt_time:.4f} seconds',
            'rounds': 12
        },
        'argon2': {
            'hash': argon2_hash,
            'time': f'{argon2_time:.4f} seconds',
            'params': f'time={ph.time_cost}, memory={ph.memory_cost}KB, parallel={ph.parallelism}'
        },
        'recommendation': 'Argon2 lebih modern dan lebih aman untuk aplikasi baru'
    })

@app.route('/api/hash/compare', methods=['POST'])
@login_required
def api_hash_compare():
    data = request.get_json()
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    algorithm = data.get('algorithm', 'sha256')
    
    if not text1 or not text2:
        return jsonify({'error': 'Kedua text harus diisi'}), 400
    
    import hashlib
    
    # Hash both texts
    hash_funcs = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }
    
    if algorithm not in hash_funcs:
        return jsonify({'error': 'Algoritma tidak didukung'}), 400
    
    hash_func = hash_funcs[algorithm]
    hash1 = hash_func(text1.encode()).hexdigest()
    hash2 = hash_func(text2.encode()).hexdigest()
    
    return jsonify({
        'text1_hash': hash1,
        'text2_hash': hash2,
        'match': hash1 == hash2,
        'algorithm': algorithm
    })

@app.route('/api/hash/password-strength', methods=['POST'])
@login_required
def api_password_strength():
    data = request.get_json()
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password harus diisi'}), 400
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append('Password terlalu pendek (minimal 8 karakter)')
    
    # Contains uppercase
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append('Tambahkan huruf besar')
    
    # Contains lowercase
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append('Tambahkan huruf kecil')
    
    # Contains digit
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append('Tambahkan angka')
    
    # Contains special character
    if any(not c.isalnum() for c in password):
        score += 1
    else:
        feedback.append('Tambahkan karakter spesial (!@#$%^&*)')
    
    # Strength rating
    if score <= 2:
        strength = 'Lemah'
    elif score <= 3:
        strength = 'Cukup'
    elif score <= 4:
        strength = 'Kuat'
    else:
        strength = 'Sangat Kuat'
    
    return jsonify({
        'score': score,
        'strength': strength,
        'length': len(password),
        'feedback': feedback
    })

# MODERN ENCRYPTION APIs - Premium Features
@app.route('/api/aes', methods=['POST'])
@login_required
def api_aes():
    data = request.get_json()
    text = data.get('text', '')
    key = data.get('key', '')
    mode = data.get('mode', 'encrypt')
    
    try:
        if mode == 'encrypt':
            result, iv = aes_encrypt(text, key)
            return jsonify({'result': result, 'iv': iv})
        else:
            iv = data.get('iv', '')
            result = aes_decrypt(text, key, iv)
            return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ============ RSA ENDPOINTS ============
@app.route('/api/rsa/generate', methods=['POST'])
@login_required
def api_rsa_generate():
    try:
        public_key, private_key = generate_keypair(bits=16)
        
        return jsonify({
            'success': True,
            'public_key': list(public_key),
            'private_key': list(private_key)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/rsa/encrypt', methods=['POST'])
@login_required
def api_rsa_encrypt():
    try:
        data = request.get_json()
        text = data.get('text', '')
        public_key = tuple(data.get('public_key', []))
        
        ciphertext = rsa_encrypt(text, public_key)
        ciphertext_string = ciphertext_to_string(ciphertext)
        
        return jsonify({
            'success': True,
            'ciphertext': ciphertext,
            'ciphertext_string': ciphertext_string
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/rsa/decrypt', methods=['POST'])
@login_required
def api_rsa_decrypt():
    try:
        data = request.get_json()
        ciphertext = data.get('ciphertext', [])
        private_key = tuple(data.get('private_key', []))
        
        plaintext = rsa_decrypt(ciphertext, private_key)
        
        return jsonify({
            'success': True,
            'plaintext': plaintext
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# =============== API ENDPOINTS FOR DASHBOARD ===============
@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """API endpoint untuk dashboard stats"""
    data = get_dashboard_data(current_user.id)
    return jsonify({
        'success': True,
        'data': data
    })

@app.route('/api/dashboard/cipher-progress', methods=['GET'])
@login_required
def api_cipher_progress():
    """API endpoint untuk cipher progress"""
    data = get_cipher_progress_data(current_user.id)
    return jsonify({
        'success': True,
        'data': data
    })

@app.route('/api/dashboard/update-streak', methods=['POST'])
@login_required
def api_update_streak():
    """API endpoint untuk update streak"""
    progress = get_user_progress(current_user.id)
    today = date.today()
    
    if progress.last_active_date != today:
        if (today - progress.last_active_date).days == 1:
            progress.current_streak += 1
        else:
            progress.current_streak = 1
        progress.last_active_date = today
        db.session.commit()
    
    return jsonify({
        'success': True,
        'streak_days': progress.current_streak
    })

@app.route('/api/dashboard/activities', methods=['GET'])
@login_required
def api_recent_activities():
    """API endpoint untuk recent activities"""
    activities = UserActivity.query.filter_by(user_id=current_user.id)\
        .order_by(UserActivity.timestamp.desc())\
        .limit(10).all()
    
    activities_data = [{
        'id': act.id,
        'type': act.activity_type,
        'description': act.description,
        'timestamp': act.timestamp.strftime('%Y-%m-d %H:%M:%S'),
        'xp_gained': act.xp_gained
    } for act in activities]
    
    return jsonify({
        'success': True,
        'activities': activities_data
    })

@app.route('/api/user/score')
@login_required
def get_user_score():
    """Get current user score and level"""
    progress = get_user_progress(current_user.id)
    return jsonify({
        'level': progress.level,
        'xp': progress.xp,
        'challenges_completed': progress.challenges_completed,
        'encryptions_performed': progress.encryptions_performed,
        'learning_time': progress.learning_time_minutes,
        'current_streak': progress.current_streak
    })

# =============== PREMIUM FEATURES ===============
@app.route('/api/premium/check', methods=['GET'])
@login_required
def api_check_premium():
    """Check user premium status"""
    is_premium = hasattr(current_user, 'is_premium') and current_user.is_premium
    return jsonify({
        'success': True,
        'is_premium': is_premium,
        'premium_expires': session.get('premium_expires')
    })

@app.route('/api/premium/simulate-upgrade', methods=['POST'])
@login_required
def api_simulate_premium_upgrade():
    """Simulate premium upgrade (for demo)"""
    try:
        plan = request.json.get('plan', 'yearly')
        
        # Simulate upgrade
        current_user.is_premium = True
        
        # Set expiration date
        if plan == 'monthly':
            expires = datetime.utcnow() + timedelta(days=30)
        elif plan == 'yearly':
            expires = datetime.utcnow() + timedelta(days=365)
        else:
            expires = datetime.utcnow() + timedelta(days=3650)  # lifetime
        
        # Store in session
        session['premium_expires'] = expires.isoformat()
        
        # Give XP bonus
        progress = get_user_progress(current_user.id)
        progress.xp += 500
        db.session.commit()
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            activity_type='premium_upgrade',
            description=f'Upgraded to {plan} premium plan',
            xp_gained=500
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Premium upgrade successful!',
            'is_premium': True,
            'premium_expires': expires.isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# =============== API ENDPOINTS FOR LEARNING ===============
@app.route('/api/learn/modules', methods=['GET'])
@login_required
def api_learn_modules():
    """Get all learning modules with user progress"""
    modules = LearningModule.query.order_by(LearningModule.order).all()
    
    modules_data = []
    for module in modules:
        progress = UserModuleProgress.query.filter_by(
            user_id=current_user.id,
            module_id=module.id
        ).first()
        
        modules_data.append({
            'id': module.id,
            'title': module.title,
            'description': module.description,
            'difficulty': module.difficulty,
            'estimated_time': module.estimated_time,
            'is_premium': module.is_premium,
            'completed': progress.completed if progress else False,
            'progress': progress.progress_percentage if progress else 0,
            'time_spent': progress.time_spent if progress else 0
        })
    
    return jsonify({
        'success': True,
        'modules': modules_data
    })

@app.route('/api/learn/videos', methods=['GET'])
@login_required
def api_learn_videos():
    """Get all video courses with user progress"""
    videos = VideoCourse.query.all()
    
    videos_data = []
    for video in videos:
        progress = UserVideoProgress.query.filter_by(
            user_id=current_user.id,
            video_id=video.id
        ).first()
        
        videos_data.append({
            'id': video.id,
            'title': video.title,
            'description': video.description,
            'url': video.url,
            'duration': video.duration,
            'thumbnail': video.thumbnail,
            'instructor': video.instructor,
            'is_premium': video.is_premium,
            'category': video.category,
            'watched': progress.watched if progress else False,
            'progress': progress.progress if progress else 0,
            'last_position': progress.last_position if progress else 0
        })
    
    return jsonify({
        'success': True,
        'videos': videos_data
    })

@app.route('/api/learn/glossary', methods=['GET'])
def api_learn_glossary():
    """Get glossary terms"""
    category = request.args.get('category', '')
    
    query = GlossaryTerm.query
    
    if category:
        query = query.filter_by(category=category)
    
    terms = query.order_by(GlossaryTerm.term).all()
    
    terms_data = [{
        'id': term.id,
        'term': term.term,
        'definition': term.definition,
        'category': term.category,
        'example': term.example,
        'related_terms': term.related_terms.split(',') if term.related_terms else []
    } for term in terms]
    
    # Get unique categories
    categories = db.session.query(GlossaryTerm.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return jsonify({
        'success': True,
        'terms': terms_data,
        'categories': categories
    })

@app.route('/api/learn/track-progress', methods=['POST'])
@login_required
def api_track_learn_progress():
    """Track learning progress"""
    try:
        data = request.json
        module_id = data.get('module_id')
        video_id = data.get('video_id')
        progress = data.get('progress', 0)
        time_spent = data.get('time_spent', 0)  # in minutes
        
        if module_id:
            # Track module progress
            user_progress = UserModuleProgress.query.filter_by(
                user_id=current_user.id,
                module_id=module_id
            ).first()
            
            if not user_progress:
                user_progress = UserModuleProgress(
                    user_id=current_user.id,
                    module_id=module_id
                )
                db.session.add(user_progress)
            
            user_progress.progress_percentage = progress
            user_progress.time_spent += time_spent
            
            if progress >= 100 and not user_progress.completed:
                user_progress.completed = True
                user_progress.completed_at = datetime.utcnow()
                
                # Give XP reward
                module = LearningModule.query.get(module_id)
                xp_earned = 100 if module.difficulty == 'easy' else 200 if module.difficulty == 'medium' else 300
                update_user_xp(current_user.id, xp_earned, 'module_completion')
                
                # Log activity
                activity = UserActivity(
                    user_id=current_user.id,
                    activity_type='learning',
                    description=f'Completed module: {module.title}',
                    xp_gained=xp_earned
                )
                db.session.add(activity)
        
        elif video_id:
            # Track video progress
            user_progress = UserVideoProgress.query.filter_by(
                user_id=current_user.id,
                video_id=video_id
            ).first()
            
            if not user_progress:
                user_progress = UserVideoProgress(
                    user_id=current_user.id,
                    video_id=video_id
                )
                db.session.add(user_progress)
            
            user_progress.progress = progress
            user_progress.last_position = data.get('last_position', 0)
            user_progress.last_watched = datetime.utcnow()
            
            if progress >= 95 and not user_progress.watched:
                user_progress.watched = True
                
                # Give XP reward
                video = VideoCourse.query.get(video_id)
                xp_earned = 50
                update_user_xp(current_user.id, xp_earned, 'video_watched')
        
        # Update total learning time
        user_progress_obj = get_user_progress(current_user.id)
        user_progress_obj.learning_time_minutes += time_spent
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# =============== CHATBOT API ===============
@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    try:
        data = request.json
        user_message = data.get('message', '').strip().lower()
        user_id = session.get('user_id', 'anonymous')
        
        # Get bot response
        bot_response = get_chatbot_response(user_message)
        
        return jsonify({
            'success': True,
            'response': bot_response['answer'],
            'follow_up': bot_response.get('follow_up', []),
            'tags': bot_response.get('tags', [])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Maaf, terjadi kesalahan. Silakan coba lagi.'
        }), 500

# =============== DEBUG ENDPOINTS ===============
@app.route('/debug/auth-test')
def debug_auth_test():
    """Test authentication endpoint"""
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None,
        'session_user_id': session.get('_user_id'),
        'session_keys': list(session.keys()),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/debug/reload-user', methods=['POST'])
@login_required
def debug_reload_user():
    """Force reload user from database"""
    try:
        # Reload user from database
        db.session.refresh(current_user)
        return jsonify({
            'success': True,
            'message': f'User reloaded: {current_user.username}',
            'user_id': current_user.id,
            'username': current_user.username
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/debug/session-dump')
def debug_session_dump():
    """Dump complete session info"""
    return jsonify({
        'session': dict(session),
        'current_user': {
            'is_authenticated': current_user.is_authenticated,
            'id': current_user.id if current_user.is_authenticated else None,
            'username': current_user.username if current_user.is_authenticated else None
        },
        'cookies': dict(request.cookies),
        'headers': dict(request.headers),
        'endpoint': request.endpoint,
        'blueprint': request.blueprint,
        'view_args': request.view_args
    })

# =============== ERROR HANDLERS ===============
@app.errorhandler(401)
def unauthorized(e):
    flash('Anda tidak memiliki akses. Silakan login terlebih dahulu.', 'danger')
    return redirect(url_for('login'))

@app.errorhandler(403)
def forbidden(e):
    flash('Akses ditolak.', 'danger')
    return redirect(url_for('index'))

# =============== DATABASE INITIALIZATION ===============
def init_tutorials_data():
    """Initialize tutorial data"""
    print("📚 Inisialisasi data tutorial...")
    
    if TutorialCategory.query.count() == 0:
        categories = [
            {
                'name': 'Fundamental Concepts',
                'slug': 'fundamentals',
                'description': 'Pengenalan kriptografi: definisi, tujuan, sejarah, terminologi, dan konsep keamanan dasar.',
                'icon': 'fas fa-brain',
                'color': '#667eea',
                'is_premium': False,
                'order': 1
            },
            {
                'name': 'Classical Cryptography',
                'slug': 'classical',
                'description': 'Cipher bersejarah: Caesar, Vigenère, Playfair, Enigma, dan teknik cryptanalysis klasik.',
                'icon': 'fas fa-history',
                'color': '#f093fb',
                'is_premium': False,
                'order': 2
            },
            {
                'name': 'Mathematical Foundations',
                'slug': 'mathematics',
                'description': 'Teori bilangan, aljabar abstrak, finite fields, probability, dan complexity theory.',
                'icon': 'fas fa-calculator',
                'color': '#4facfe',
                'is_premium': False,
                'order': 3
            },
            {
                'name': 'Symmetric Cryptography',
                'slug': 'symmetric',
                'description': 'DES, AES, Twofish, Serpent, mode operasi, dan implementasi modern.',
                'icon': 'fas fa-key',
                'color': '#43e97b',
                'is_premium': False,
                'order': 4
            },
            {
                'name': 'Asymmetric Cryptography',
                'slug': 'asymmetric',
                'description': 'RSA, ECC, DH, DSA, elliptic curves, dan aplikasi praktis.',
                'icon': 'fas fa-lock-open',
                'color': '#fa709a',
                'is_premium': True,
                'order': 5
            },
            {
                'name': 'Advanced Cryptography',
                'slug': 'advanced',
                'description': 'Post-quantum, homomorphic, zero-knowledge, MPC, dan kriptografi modern.',
                'icon': 'fas fa-rocket',
                'color': '#a8edea',
                'is_premium': True,
                'order': 6
            }
        ]
        
        for cat_data in categories:
            category = TutorialCategory(**cat_data)
            db.session.add(category)
        
        db.session.commit()
    
    if Tutorial.query.count() == 0:
        tutorials = [
            {
                'title': 'Apa itu Kriptografi? Pengertian Dasar',
                'slug': 'what-is-cryptography',
                'description': 'Memahami definisi, tujuan, dan prinsip dasar kriptografi. Confidentiality, integrity, authentication, non-repudiation.',
                'content': '''
                    <h2>Pengenalan Kriptografi</h2>
                    <p>Kriptografi (dari bahasa Yunani: κρυπτός, "tersembunyi, rahasia"; dan γράφειν, "menulis") adalah praktik dan studi teknik untuk komunikasi yang aman di hadapan pihak ketiga yang tidak diinginkan.</p>
                    
                    <h3>Prinsip Dasar Keamanan (CIA Triad):</h3>
                    <ul>
                        <li><strong>Confidentiality (Kerahasiaan):</strong> Informasi hanya dapat diakses oleh pihak yang berwenang</li>
                        <li><strong>Integrity (Integritas):</strong> Informasi tidak dapat diubah tanpa otorisasi</li>
                        <li><strong>Authentication (Autentikasi):</strong> Memverifikasi identitas pengirim dan penerima</li>
                    </ul>
                ''',
                'difficulty': 'beginner',
                'duration_minutes': 20,
                'category': 'Fundamental Concepts',
                'tags': 'Dasar,Konsep,Terminologi,Pengenalan',
                'is_premium': False,
                'is_new': True,
                'featured': True,
                'estimated_reading_time': 15,
                'order': 1
            },
            {
                'title': 'Caesar Cipher: Cipher Pertama dalam Sejarah',
                'slug': 'caesar-cipher',
                'description': 'Pelajari cipher substitusi paling terkenal yang digunakan Julius Caesar untuk komunikasi militer rahasia.',
                'content': '''
                    <h2>Caesar Cipher</h2>
                    <p>Cipher substitusi sederhana di mana setiap huruf digeser sejumlah posisi tertentu dalam alfabet.</p>
                    
                    <h3>Implementasi Python:</h3>
                    <pre><code>def caesar_cipher(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        else:
            result += char
    return result</code></pre>
                ''',
                'difficulty': 'beginner',
                'duration_minutes': 30,
                'category': 'Classical Cryptography',
                'tags': 'Substitusi,Sejarah,Python,Dasar',
                'is_premium': False,
                'is_new': True,
                'featured': True,
                'estimated_reading_time': 25,
                'order': 2
            },
            {
                'title': 'RSA Encryption: Kriptografi Kunci Publik',
                'slug': 'rsa-encryption',
                'description': 'Pelajari matematika di balik RSA, algoritma yang mengamankan internet modern. Teori bilangan prima dan modulasi.',
                'content': '''
                    <h2>RSA Cryptosystem</h2>
                    <p>RSA (Rivest-Shamir-Adleman) adalah algoritma kriptografi kunci publik yang digunakan untuk enkripsi dan tanda tangan digital.</p>
                    
                    <h3>Matematika di Balik RSA:</h3>
                    <ul>
                        <li><strong>Dasar:</strong> Kesulitan memfaktorkan bilangan besar</li>
                        <li><strong>Euler's Theorem:</strong> a^φ(n) ≡ 1 (mod n)</li>
                        <li><strong>Chinese Remainder Theorem:</strong> Mempercepat dekripsi</li>
                    </ul>
                ''',
                'difficulty': 'advanced',
                'duration_minutes': 150,
                'category': 'Asymmetric Cryptography',
                'tags': 'Asimetris,Kunci Publik,Matematika,Python,Prime',
                'is_premium': True,
                'is_new': False,
                'featured': True,
                'estimated_reading_time': 120,
                'order': 3
            }
        ]
        
        for tut_data in tutorials:
            tutorial = Tutorial(**tut_data)
            db.session.add(tutorial)
        
        db.session.commit()
        print("✅ Data tutorial diinisialisasi")
        
def init_learning_data():
    """Initialize learning data"""
    print("📚 Inisialisasi data pembelajaran...")
    
    # Add learning modules
    if LearningModule.query.count() == 0:
        modules = [
            {
                'title': 'Pengantar Kriptografi',
                'description': 'Memahami konsep dasar kriptografi dan sejarahnya',
                'content': '... full content ...',
                'difficulty': 'beginner',
                'estimated_time': 30,
                'category': 'Dasar Kriptografi',
                'is_premium': False,
                'order': 1
            },
            {
                'title': 'Caesar Cipher',
                'description': 'Mempelajari cipher substitusi paling dasar',
                'content': '... full content ...',
                'difficulty': 'beginner',
                'estimated_time': 45,
                'category': 'Cipher Klasik',
                'is_premium': False,
                'order': 2
            },
            {
                'title': 'Vigenère Cipher',
                'description': 'Cipher polialfabetik yang lebih aman',
                'content': '... full content ...',
                'difficulty': 'intermediate',
                'estimated_time': 60,
                'category': 'Cipher Klasik',
                'is_premium': False,
                'order': 3
            },
            {
                'title': 'RSA Encryption',
                'description': 'Algoritma kriptografi kunci publik modern',
                'content': '... full content ...',
                'difficulty': 'advanced',
                'estimated_time': 90,
                'category': 'Kriptografi Modern',
                'is_premium': True,
                'order': 4
            },
            {
                'title': 'Hash Functions',
                'description': 'Fungsi hash untuk keamanan password dan integritas data',
                'content': '... full content ...',
                'difficulty': 'intermediate',
                'estimated_time': 50,
                'category': 'Kriptografi Modern',
                'is_premium': False,
                'order': 5
            },
            {
                'title': 'Blockchain & Cryptocurrency',
                'description': 'Aplikasi kriptografi dalam teknologi blockchain',
                'content': '... full content ...',
                'difficulty': 'advanced',
                'estimated_time': 75,
                'category': 'Aplikasi Praktis',
                'is_premium': True,
                'order': 6
            }
        ]
        
        for module_data in modules:
            module = LearningModule(**module_data)
            db.session.add(module)
    
    # Add achievements for modules
    if Achievement.query.filter_by(requirement='module_novice').count() == 0:
        module_achievements = [
            Achievement(
                name='Module Novice',
                description='Selesaikan modul pembelajaran pertama',
                icon='fas fa-graduation-cap',
                xp_reward=50,
                requirement='module_novice'
            ),
            Achievement(
                name='Module Explorer',
                description='Selesaikan 5 modul pembelajaran',
                icon='fas fa-compass',
                xp_reward=100,
                requirement='module_explorer'
            ),
            Achievement(
                name='Module Master',
                description='Selesaikan 10 modul pembelajaran',
                icon='fas fa-crown',
                xp_reward=200,
                requirement='module_master'
            )
        ]
        
        for ach in module_achievements:
            db.session.add(ach)
    
    db.session.commit()
    print("✅ Data pembelajaran diinisialisasi")

def initialize_database():
    """Initialize database dengan data default"""
    print("🔧 Inisialisasi database...")
    db.create_all()
    print("✅ Tabel database dibuat")
    
    if Achievement.query.count() == 0:
        achievements = [
            Achievement(
                name='Caesar Novice',
                description='Selesaikan quiz Caesar Cipher pertama',
                icon='fas fa-crown',
                xp_reward=50,
                requirement='complete_caesar_quiz'
            ),
            Achievement(
                name='Shift Master',
                description='Selesaikan semua challenge Caesar Cipher',
                icon='fas fa-trophy',
                xp_reward=100,
                requirement='complete_all_caesar_challenges'
            ),
            Achievement(
                name='Vigenere Explorer',
                description='Selesaikan quiz Vigenere Cipher',
                icon='fas fa-key',
                xp_reward=75,
                requirement='complete_vigenere_quiz'
            ),
        ]
        
        for a in achievements:
            db.session.add(a)
        
        db.session.commit()
        print("✅ Data achievements ditambahkan")
    
    # Initialize learning modules
    init_learning_data()
    
    # Tambah contoh notifikasi tanpa menggunakan url_for()
    print("📢 Membuat notifikasi contoh...")
    if User.query.count() > 0 and Notification.query.count() == 0:
        users = User.query.all()
        for user in users:
            # Gunakan URL string langsung tanpa url_for()
            welcome_notif = Notification(
                user_id=user.id,
                title='Selamat Datang di DecoDify! 🎉',
                message='Selamat bergabung di platform belajar kriptografi terbaik. Mulai petualangan kriptomu sekarang!',
                notification_type='success',
                link='/learn'  # URL string langsung
            )
            db.session.add(welcome_notif)
            
            caesar_notif = Notification(
                user_id=user.id,
                title='Pelajari Caesar Cipher',
                message='Coba cipher pertama: Caesar Cipher. Geser huruf untuk enkripsi dan dekripsi!',
                notification_type='info',
                link='/caesar'  # URL string langsung
            )
            db.session.add(caesar_notif)
        
        db.session.commit()
        print("✅ Notifikasi contoh ditambahkan")
    
    print("🎉 Database berhasil diinisialisasi!")

# =============== FORCE RECREATE DATABASE ===============
def force_recreate_db():
    """Force recreate database - untuk development saja!"""
    print("\n" + "="*60)
    print("🚨 FORCE RECREATING DATABASE...")
    print("="*60)
    
    # Drop semua tabel
    db.drop_all()
    print("✅ Semua tabel di-drop")
    
    # Buat semua tabel baru
    db.create_all()
    print("✅ Tabel baru dibuat")
    
    # Inisialisasi data
    initialize_database()
    print("✅ Data diinisialisasi")
    
    print("🎉 Database berhasil direcreate!")
    print("="*60 + "\n")

# Tambahkan route untuk trigger reset
@app.route('/force-reset')
def force_reset():
    """Route untuk force reset database"""
    if app.debug:
        force_recreate_db()
        return '''
        <h1>✅ Database Berhasil Direset!</h1>
        <p>Semua tabel telah direcreate dengan skema terbaru.</p>
        <p>Silakan <a href="/">kembali ke home</a> dan login kembali.</p>
        '''
    return '<h1>Hanya tersedia di mode debug</h1>'

@app.route('/reset-db', methods=['GET', 'POST'])
def reset_database():
    """Route untuk reset database (HANYA UNTUK DEVELOPMENT!)"""
    if request.method == 'GET':
        return '''
        <h1>Reset Database</h1>
        <p>Ini akan menghapus semua data!</p>
        <form method="POST">
            <input type="hidden" name="confirm" value="yes">
            <button type="submit" style="background: red; color: white; padding: 10px 20px;">
                Reset Database
            </button>
        </form>
        '''
    
    if request.method == 'POST':
        try:
            db.drop_all()
            db.create_all()
            
            achievements = [
                Achievement(
                    name='Caesar Novice',
                    description='Selesaikan quiz Caesar Cipher pertama',
                    icon='fas fa-crown',
                    xp_reward=50,
                    requirement='complete_caesar_quiz'
                ),
                Achievement(
                    name='Shift Master',
                    description='Selesaikan semua challenge Caesar Cipher',
                    icon='fas fa-trophy',
                    xp_reward=100,
                    requirement='complete_all_caesar_challenges'
                ),
                Achievement(
                    name='Crypto Learner',
                    description='Gunakan 5 cipher berbeda',
                    icon='fas fa-graduation-cap',
                    xp_reward=150,
                    requirement='use_5_ciphers'
                )
            ]
            for ach in achievements:
                db.session.add(ach)
            
            db.session.commit()
            
            return '''
            <h1>Database Berhasil Direset!</h1>
            <p>Semua tabel telah di-recreate dengan schema baru.</p>
            <a href="/">Kembali ke Home</a>
            '''
            
        except Exception as e:
            return f'<h1>Error: {str(e)}</h1>'

# =============== FIX DATABASE COLUMNS ===============
def add_missing_columns():
    """Tambahkan kolom yang hilang ke tabel user"""
    print("🛠️  Memperbaiki struktur tabel user...")
    
    try:
        import sqlite3
        import os
        
        # Pastikan direktori instance ada
        os.makedirs('instance', exist_ok=True)
        
        db_path = 'instance/crypto.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Daftar kolom yang harus ada
        required_columns = [
            ('avatar', 'VARCHAR(200)'),
            ('bio', 'TEXT'),
            ('premium_expires', 'DATETIME')
        ]
        
        # Cek kolom yang sudah ada
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Tambahkan kolom yang hilang
        for col_name, col_type in required_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Kolom '{col_name}' ditambahkan")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Gagal menambah kolom {col_name}: {e}")
        
        conn.commit()
        conn.close()
        print("🎉 Perbaikan struktur tabel selesai!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# =============== MAIN ENTRY POINT ===============
if __name__ == '__main__':
    with app.app_context():
        add_missing_columns()
        # Pastikan semua tabel dibuat
        db.create_all()
        initialize_database()
    
    app.run(debug=True, host='0.0.0.0', port=5000)