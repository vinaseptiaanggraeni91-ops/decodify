from utils.caesar import caesar_decrypt

def bruteforce_caesar(ciphertext):
    """
    Bruteforce Caesar Cipher dengan mencoba semua shift (0-25)
    
    Args:
        ciphertext (str): Teks terenkripsi
    
    Returns:
        list: List dictionary dengan shift dan hasil dekripsi
    """
    results = []
    
    for shift in range(26):
        decrypted = caesar_decrypt(ciphertext, shift)
        
        # Ngitung score pikeun nangtukeun sabaraha mirip jeung basa Inggris
        # Ngetangkeun teks anu paling mirip jeung basa Inggris
        score = calculate_english_score(decrypted)
        
        results.append({
            'shift': shift,
            'text': decrypted,
            'score': score
        })
    
    # Urutkan berdasarkan score tertinggi
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


def calculate_english_score(text):
    """
    Hitung score berdasarkan frekuensi karakter bahasa Inggris
    Semakin tinggi score, semakin mirip dengan teks bahasa Inggris
    
    Args:
        text (str): Teks yang akan dianalisis
    
    Returns:
        float: Score teks
    """
    # mun ieu teh daptar karakter umum dina basa Inggris
    common_chars = 'ETAOINSHRDLCUMWFGYPBVKJXQZ'
    
    score = 0
    text_upper = text.upper()
    
    # poin pikeun spasi (karakter umum)
    score += text.count(' ') * 2
    
    # poin pikeun karakter umum
    for i, char in enumerate(common_chars):
        if char in text_upper:
            # kanggo unggal karakter umum, tambahkeun poin nurutkeun posisina
            score += (26 - i) * text_upper.count(char)
    
    return score


def frequency_analysis(text):
    """
    Analisis frekuensi karakter dalam teks
    Berguna untuk cryptanalysis
    
    Args:
        text (str): Teks yang akan dianalisis
    
    Returns:
        dict: Dictionary berisi frekuensi setiap karakter
    """
    frequency = {}
    total_chars = 0
    
    for char in text.upper():
        if char.isalpha():
            frequency[char] = frequency.get(char, 0) + 1
            total_chars += 1
    
    # etangkeun persentase na
    percentage = {}
    for char, count in frequency.items():
        percentage[char] = {
            'count': count,
            'percentage': round((count / total_chars) * 100, 2) if total_chars > 0 else 0
        }
    
    # urutkeun berdasarkan count
    sorted_freq = sorted(percentage.items(), key=lambda x: x[1]['count'], reverse=True)
    
    return {
        'total_characters': total_chars,
        'unique_characters': len(frequency),
        'frequency': dict(sorted_freq)
    }


def bruteforce_vigenere_key_length(ciphertext, max_length=10):
    """
    Mencari kemungkinan panjang key Vigenere menggunakan Index of Coincidence
    
    Args:
        ciphertext (str): Teks terenkripsi
        max_length (int): Panjang key maksimum yang dicoba
    
    Returns:
        list: List kemungkinan panjang key dengan scorenya
    """
    # bersihkeun teks tina karakter anu sanes alfabet
    clean_text = ''.join(c for c in ciphertext.upper() if c.isalpha())
    
    if len(clean_text) < 2:
        return []
    
    results = []
    
    for key_length in range(1, min(max_length + 1, len(clean_text))):
        # itung IC pikeun tiap subsequence
        ic_sum = 0
        
        for i in range(key_length):
            subsequence = clean_text[i::key_length]
            ic = calculate_ic(subsequence)
            ic_sum += ic
        
        avg_ic = ic_sum / key_length
        
        results.append({
            'key_length': key_length,
            'ic_score': round(avg_ic, 4)
        })
    
    # urutkeun didasarkeun kana deukeutna ka IC basa Inggris (~0.065)
    results.sort(key=lambda x: abs(x['ic_score'] - 0.065))
    
    return results


def calculate_ic(text):
    """
    Hitung Index of Coincidence (IC)
    IC untuk bahasa Inggris ~ 0.065
    IC untuk teks random ~ 0.038
    
    Args:
        text (str): Teks yang akan dihitung IC-nya
    
    Returns:
        float: Nilai IC
    """
    if len(text) < 2:
        return 0
    
    # itung frekuensi karakter
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    
    # itung IC
    n = len(text)
    ic_sum = sum(f * (f - 1) for f in freq.values())
    ic = ic_sum / (n * (n - 1)) if n > 1 else 0
    
    return ic