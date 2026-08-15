def vigenere_encrypt(plaintext, key):
    """
    Enkripsi teks menggunakan Vigenere Cipher
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        key (str): Kata kunci untuk enkripsi
    
    Returns:
        str: Teks terenkripsi
    """
    if not key:
        return plaintext
    
    result = ""
    key = key.upper()
    key_length = len(key)
    key_index = 0
    
    for char in plaintext:
        if char.isalpha():
            # Tangtukeun base (A pikeun uppercase, a pikeun lowercase)
            base = ord('A') if char.isupper() else ord('a')
            
            # gubungkeun karakter key anu saluyu
            key_char = key[key_index % key_length]
            shift = ord(key_char) - ord('A')
            
            # Enkripsi karakter
            encrypted = (ord(char) - base + shift) % 26
            result += chr(base + encrypted)
            
            key_index += 1
        else:
            # Karakter non-alphabet teu dirobah
            result += char
    
    return result


def vigenere_decrypt(ciphertext, key):
    """
    Dekripsi teks yang dienkripsi dengan Vigenere Cipher
    
    Args:
        ciphertext (str): Teks terenkripsi
        key (str): Kata kunci yang digunakan saat enkripsi
    
    Returns:
        str: Teks asli
    """
    if not key:
        return ciphertext
    
    result = ""
    key = key.upper()
    key_length = len(key)
    key_index = 0
    
    for char in ciphertext:
        if char.isalpha():
            # Tangtukeun base (A pikeun uppercase, a pikeun lowercase)
            base = ord('A') if char.isupper() else ord('a')
            
            # Gubungkeun karakter key anu saluyu
            key_char = key[key_index % key_length]
            shift = ord(key_char) - ord('A')
            
            # Dekripsi karakter
            decrypted = (ord(char) - base - shift) % 26
            result += chr(base + decrypted)
            
            key_index += 1
        else:
            # Karakter non-alphabet teu dirobah
            result += char
    
    return result


def vigenere_analyze(ciphertext):
    """
    Analisis sederhana untuk Vigenere Cipher
    Menghitung kemungkinan panjang key
    
    Args:
        ciphertext (str): Teks terenkripsi
    
    Returns:
        dict: Informasi analisis
    """
    # Hitung frekuensi karakter
    freq = {}
    for char in ciphertext.upper():
        if char.isalpha():
            freq[char] = freq.get(char, 0) + 1
    
    # urutkeun didasarkeun frekuensi
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'length': len(ciphertext),
        'alphabetic_chars': sum(freq.values()),
        'top_5_chars': sorted_freq[:5] if sorted_freq else []
    }