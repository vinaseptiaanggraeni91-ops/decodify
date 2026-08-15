from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app import app, db
from models import UserProgress, CipherUsage, QuizQuestion, QuizAttempt, Challenge, ChallengeAttempt, UserActivity, Achievement, UserAchievement
from utils.ciphers import caesar_encrypt, caesar_decrypt
from datetime import datetime

@app.route('/caesar')
def caesar():
    if current_user.is_authenticated:
        progress = get_user_progress(current_user.id)
        return render_template('caesar.html',
                             username=current_user.username,
                             user_level=progress.level,
                             user_xp=progress.xp)
    else:
        return render_template('caesar.html',
                             username='Guest',
                             user_level=1,
                             user_xp=0)

@app.route('/api/caesar', methods=['POST'])
def api_caesar():
    data = request.get_json()
    text = data.get('text', '')
    shift = int(data.get('shift', 3))
    mode = data.get('mode', 'encrypt')
    
    try:
        if mode == 'encrypt':
            result = caesar_encrypt(text, shift)
        else:
            result = caesar_decrypt(text, shift)
        
        if current_user.is_authenticated:
            log_cipher_usage(current_user.id, 'caesar')
        
        return jsonify({
            'success': True,
            'result': result,
            'shift': shift,
            'mode': mode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/quiz/caesar/questions')
def get_caesar_quiz():
    questions = QuizQuestion.query.filter_by(cipher_name='caesar').all()
    
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

@app.route('/api/quiz/caesar/challenges')
def get_caesar_challenges():
    challenges = Challenge.query.filter_by(cipher_name='caesar').all()
    
    challenges_data = []
    for c in challenges:
        challenges_data.append({
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'ciphertext': c.ciphertext,
            'plaintext': c.plaintext,
            'hint': c.hint,
            'difficulty': c.difficulty,
            'xp': c.xp_reward,
            'category': c.category
        })
    
    return jsonify(challenges_data)

# Helper functions
def get_user_progress(user_id):
    progress = UserProgress.query.filter_by(user_id=user_id).first()
    if not progress:
        progress = UserProgress(user_id=user_id)
        db.session.add(progress)
        db.session.commit()
    return progress

def update_user_xp(user_id, xp_earned, activity_type="quiz"):
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

def log_cipher_usage(user_id, cipher_name):
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