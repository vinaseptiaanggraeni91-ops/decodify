def caesar_encrypt(text, shift):
    """
    Enkripsi teks menggunakan Caesar Cipher
    
    Args:
        text (str): Teks yang akan dienkripsi
        shift (int): Jumlah pergeseran (0-25)
    
    Returns:
        str: Teks terenkripsi
    """
    result = ""
    shift = shift % 26  # pastikeun shift di antara 0-25
    
    for char in text:
        if char.isalpha():
            # Tentukeun basis ASCII
            base = ord('A') if char.isupper() else ord('a')
            # Eserkeun karakter
            shifted = (ord(char) - base + shift) % 26
            result += chr(base + shifted)
        else:
            # Teu ngarobah karakter non-alfabet
            result += char
    
    return result


def caesar_decrypt(text, shift):
    """
    Dekripsi teks yang dienkripsi dengan Caesar Cipher
    
    Args:
        text (str): Teks terenkripsi
        shift (int): Jumlah pergeseran yang digunakan saat enkripsi
    
    Returns:
        str: Teks asli
    """
    # dekripsi nyaéta enkripsi jeung shift negatif
    return caesar_encrypt(text, -shift)


def caesar_crack(ciphertext):
    """
    Bruteforce Caesar Cipher dengan mencoba semua kemungkinan shift
    
    Args:
        ciphertext (str): Teks terenkripsi
    
    Returns:
        list: List dictionary berisi shift dan hasil dekripsi
    """
    results = []
    
    for shift in range(26):
        decrypted = caesar_decrypt(ciphertext, shift)
        results.append({
            'shift': shift,
            'text': decrypted
        })
    
    return results