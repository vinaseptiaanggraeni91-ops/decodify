"""
Enhanced Hash Utilities dengan Deteksi Angka
Support: MD5, SHA-1, SHA-256, SHA-512, Bcrypt, Argon2
"""

import hashlib
import re

def hash_all(text):
    """Generate hash dengan berbagai algoritma"""
    return {
        'md5': hashlib.md5(text.encode()).hexdigest(),
        'sha1': hashlib.sha1(text.encode()).hexdigest(),
        'sha256': hashlib.sha256(text.encode()).hexdigest(),
        'sha512': hashlib.sha512(text.encode()).hexdigest(),
        'sha3_256': hashlib.sha3_256(text.encode()).hexdigest(),
        'blake2b': hashlib.blake2b(text.encode()).hexdigest(),
    }

def compare_hashes(text1, text2, algorithm='sha256'):
    """Compare hash dari dua text"""
    hash_func = getattr(hashlib, algorithm)
    hash1 = hash_func(text1.encode()).hexdigest()
    hash2 = hash_func(text2.encode()).hexdigest()
    
    return {
        'text1_hash': hash1,
        'text2_hash': hash2,
        'match': hash1 == hash2,
        'algorithm': algorithm
    }

def detect_numbers(text):
    """
    Deteksi angka dalam text
    Requirement dari dosen: "Angka harus bisa ke deteksi"
    """
    # Cari semua angka dalam text
    numbers = re.findall(r'\d+', text)
    
    # Hitung statistik
    total_numbers = len(numbers)
    total_digits = sum(len(num) for num in numbers)
    
    # Cari angka unik
    unique_numbers = list(set(numbers))
    
    # Deteksi pola angka
    has_sequence = any(
        str(i) + str(i+1) + str(i+2) in text 
        for i in range(8)  # 012, 123, 234, dst
    )
    
    has_repeated = any(
        str(i) * 3 in text 
        for i in range(10)  # 000, 111, 222, dst
    )
    
    return {
        'contains_numbers': total_numbers > 0,
        'numbers_found': numbers,
        'total_numbers': total_numbers,
        'total_digits': total_digits,
        'unique_numbers': unique_numbers,
        'has_sequence': has_sequence,
        'has_repeated_digits': has_repeated,
        'percentage': (total_digits / len(text) * 100) if len(text) > 0 else 0
    }

def password_strength_check(password):
    """
    Check password strength dengan deteksi angka
    """
    # Deteksi angka
    number_info = detect_numbers(password)
    
    # Kriteria password
    length = len(password)
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    # Hitung score
    score = 0
    feedback = []
    
    # Length
    if length >= 12:
        score += 2
        feedback.append('✓ Panjang password baik (≥12 karakter)')
    elif length >= 8:
        score += 1
        feedback.append('⚠ Panjang password cukup (8-11 karakter)')
    else:
        feedback.append('✗ Password terlalu pendek (<8 karakter)')
    
    # Uppercase
    if has_upper:
        score += 1
        feedback.append('✓ Mengandung huruf besar')
    else:
        feedback.append('✗ Tidak ada huruf besar')
    
    # Lowercase
    if has_lower:
        score += 1
        feedback.append('✓ Mengandung huruf kecil')
    else:
        feedback.append('✗ Tidak ada huruf kecil')
    
    # Digits (REQUIREMENT DOSEN)
    if has_digit:
        score += 1
        if number_info['total_numbers'] >= 2:
            score += 1
            feedback.append(f'✓ Mengandung {number_info["total_numbers"]} angka')
        else:
            feedback.append('✓ Mengandung angka')
        
        # Warning untuk pola angka
        if number_info['has_sequence']:
            score -= 1
            feedback.append('⚠ Hindari urutan angka (123, 234, dll)')
        if number_info['has_repeated_digits']:
            score -= 1
            feedback.append('⚠ Hindari angka berulang (111, 222, dll)')
    else:
        feedback.append('✗ Tidak ada angka (WAJIB!)')
    
    # Special characters
    if has_special:
        score += 1
        feedback.append('✓ Mengandung karakter khusus')
    else:
        feedback.append('✗ Tidak ada karakter khusus')
    
    # Determine strength
    if score >= 6:
        strength = 'Sangat Kuat'
        color = 'success'
    elif score >= 4:
        strength = 'Kuat'
        color = 'primary'
    elif score >= 2:
        strength = 'Sedang'
        color = 'warning'
    else:
        strength = 'Lemah'
        color = 'danger'
    
    return {
        'strength': strength,
        'score': score,
        'max_score': 7,
        'color': color,
        'feedback': feedback,
        'number_analysis': number_info,
        'criteria': {
            'length': length,
            'has_uppercase': has_upper,
            'has_lowercase': has_lower,
            'has_digit': has_digit,
            'has_special': has_special
        }
    }

def validate_input_contains_numbers(text):
    """
    Validasi khusus: apakah input mengandung angka
    Untuk form validation
    """
    number_info = detect_numbers(text)
    
    if not number_info['contains_numbers']:
        return {
            'valid': False,
            'error': 'Input harus mengandung minimal 1 angka!'
        }
    
    return {
        'valid': True,
        'numbers_found': number_info['numbers_found']
    }

def analyze_text_composition(text):
    """
    Analisis komposisi text: huruf, angka, simbol
    """
    total_chars = len(text)
    
    letters = len(re.findall(r'[a-zA-Z]', text))
    digits = len(re.findall(r'\d', text))
    spaces = len(re.findall(r'\s', text))
    special = total_chars - letters - digits - spaces
    
    return {
        'total_characters': total_chars,
        'letters': letters,
        'digits': digits,
        'spaces': spaces,
        'special_chars': special,
        'composition': {
            'letters_percent': (letters / total_chars * 100) if total_chars > 0 else 0,
            'digits_percent': (digits / total_chars * 100) if total_chars > 0 else 0,
            'spaces_percent': (spaces / total_chars * 100) if total_chars > 0 else 0,
            'special_percent': (special / total_chars * 100) if total_chars > 0 else 0,
        }
    }

if __name__ == '__main__':
    # Test deteksi angka
    test_text = "Hello123World456"
    print("=== Test Deteksi Angka ===")
    result = detect_numbers(test_text)
    print(f"Text: {test_text}")
    print(f"Numbers found: {result['numbers_found']}")
    print(f"Total numbers: {result['total_numbers']}")
    
    # Test password strength
    print("\n=== Test Password Strength ===")
    test_password = "MyP@ssw0rd123"
    result = password_strength_check(test_password)
    print(f"Password: {test_password}")
    print(f"Strength: {result['strength']}")
    print(f"Score: {result['score']}/{result['max_score']}")
    print("Feedback:")
    for fb in result['feedback']:
        print(f"  {fb}")