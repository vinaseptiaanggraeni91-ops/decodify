from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app import app, db
from models import UserProgress, CipherUsage, VigenereUsage, VigenereQuizQuestion, VigenereChallenge, VigenereQuizAttempt, VigenereChallengeAttempt, UserActivity, Achievement, UserAchievement
from utils.ciphers import vigenere_encrypt, vigenere_decrypt
from datetime import datetime, date
# Di bagian atas app.py, tambahkan import
from ciphers.vigenere import vigenere_encrypt, vigenere_decrypt

@app.route('/vigenere')
def vigenere_page():
    if current_user.is_authenticated:
        progress = get_user_progress(current_user.id)
        vigenere_usage = VigenereUsage.query.filter_by(user_id=current_user.id).first()
        
        return render_template('vigenere.html',
                             username=current_user.username,
                             user_level=progress.level,
                             user_xp=progress.xp,
                             vigenere_encryptions=vigenere_usage.encryptions_count if vigenere_usage else 0,
                             vigenere_decryptions=vigenere_usage.decryptions_count if vigenere_usage else 0)
    else:
        return render_template('vigenere.html',
                             username='Guest',
                             user_level=1,
                             user_xp=0,
                             vigenere_encryptions=0,
                             vigenere_decryptions=0)

@app.route('/api/vigenere', methods=['POST'])
def api_vigenere():
    data = request.get_json()
    text = data.get('text', '')
    key = data.get('key', '').upper()
    mode = data.get('mode', 'encrypt')
    
    try:
        key = ''.join(c for c in key if c.isalpha())
        if not key:
            return jsonify({'success': False, 'error': 'Key harus mengandung huruf alfabet'})
        
        if mode == 'encrypt':
            result = vigenere_encrypt(text, key)
        else:
            result = vigenere_decrypt(text, key)
        
        if current_user.is_authenticated:
            log_vigenere_usage(current_user.id, mode)
            log_cipher_usage(current_user.id, 'vigenere')
        
        return jsonify({
            'success': True,
            'result': result,
            'key': key,
            'mode': mode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/quiz/vigenere/questions')
def get_vigenere_quiz():
    questions = VigenereQuizQuestion.query.all()
    quiz_data = []
    for q in questions:
        quiz_data.append({
            'id': q.id,
            'question': q.question,
            'options': [q.option_a, q.option_b, q.option_c, q.option_d],
            'correct': ['A', 'B', 'C', 'D'].index(q.correct_answer),
            'explanation': q.explanation,
            'difficulty': q.difficulty,
            'points': q.xp_reward
        })
    return jsonify(quiz_data)

@app.route('/api/quiz/vigenere/challenges')
def get_vigenere_challenges():
    challenges = VigenereChallenge.query.all()
    challenges_data = []
    for c in challenges:
        challenges_data.append({
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'plaintext': c.plaintext,
            'ciphertext': c.ciphertext,
            'key': c.key,
            'solution': c.solution,
            'hint': c.hint,
            'difficulty': c.difficulty,
            'xp': c.xp_reward,
            'category': c.category
        })
    return jsonify(challenges_data)

# Helper functions for vigenere
def log_vigenere_usage(user_id, mode='encrypt'):
    usage = VigenereUsage.query.filter_by(user_id=user_id).first()
    if usage:
        if mode == 'encrypt':
            usage.encryptions_count += 1
        else:
            usage.decryptions_count += 1
        usage.last_used = datetime.now()
    else:
        usage = VigenereUsage(
            user_id=user_id,
            encryptions_count=1 if mode == 'encrypt' else 0,
            decryptions_count=0 if mode == 'encrypt' else 1
        )
        db.session.add(usage)
    
    cipher_usage = CipherUsage.query.filter_by(user_id=user_id, cipher_name='vigenere').first()
    if cipher_usage:
        cipher_usage.usage_count += 1
        cipher_usage.last_used = datetime.now()
    else:
        cipher_usage = CipherUsage(
            user_id=user_id,
            cipher_name='vigenere',
            usage_count=1
        )
        db.session.add(cipher_usage)
    
    db.session.commit()

def get_user_progress(user_id):
    from routes.caesar import get_user_progress as get_progress
    return get_progress(user_id)

def log_cipher_usage(user_id, cipher_name):
    from routes.caesar import log_cipher_usage as log_usage
    log_usage(user_id, cipher_name)

def update_user_xp(user_id, xp_earned, activity_type="quiz"):
    from routes.caesar import update_user_xp as update_xp
    return update_xp(user_id, xp_earned, activity_type)