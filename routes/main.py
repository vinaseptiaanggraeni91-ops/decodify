# routes/main.py
from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from rsa import generate_keypair, rsa_encrypt, rsa_decrypt, ciphertext_to_string

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    from app import CipherUsage, UserProgress
    
    # Get user progress
    progress = UserProgress.query.filter_by(user_id=current_user.id).first()
    
    # Calculate completed ciphers
    cipher_usages = CipherUsage.query.filter_by(user_id=current_user.id).count()
    total_ciphers = 15  # Total ciphers available
    
    return render_template('dashboard.html', 
                         username=current_user.username,
                         user_level=progress.level,
                         user_xp=progress.xp,
                         completed_ciphers=cipher_usages,
                         total_ciphers=total_ciphers,
                         streak_days=progress.current_streak)


@app.route('/api/rsa/generate', methods=['POST'])
@login_required  # Hapus baris ini kalau tidak pakai login
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
@login_required  # Hapus baris ini kalau tidak pakai login
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
@login_required  # Hapus baris ini kalau tidak pakai login
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