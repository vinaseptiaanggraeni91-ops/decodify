import string
import random

def generate_substitution_key():
    """
    Generate random substitution key
    
    Returns:
        dict: Dictionary mapping huruf asli ke huruf substitusi
    """
    alphabet = list(string.ascii_uppercase)
    shuffled = alphabet.copy()
    random.shuffle(shuffled)
    
    return dict(zip(alphabet, shuffled))


def substitution_encrypt(plaintext, key=None):
    """
    Enkripsi menggunakan Substitution Cipher
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        key (dict): Dictionary substitusi, jika None akan generate random
    
    Returns:
        tuple: (ciphertext, key_used)
    """
    if key is None:
        key = generate_substitution_key()
    
    result = ""
    
    for char in plaintext:
        if char.upper() in key:
            if char.isupper():
                result += key[char]
            else:
                result += key[char.upper()].lower()
        else:
            result += char
    
    return result, key


def substitution_decrypt(ciphertext, key):
    """
    Dekripsi Substitution Cipher
    
    Args:
        ciphertext (str): Teks terenkripsi
        key (dict): Dictionary substitusi yang digunakan
    
    Returns:
        str: Teks asli
    """
    # Balikeun konci ekeur deskripsi
    reverse_key = {v: k for k, v in key.items()}
    
    result = ""
    
    for char in ciphertext:
        if char.upper() in reverse_key:
            if char.isupper():
                result += reverse_key[char]
            else:
                result += reverse_key[char.upper()].lower()
        else:
            result += char
    
    return result


def key_from_keyword(keyword):
    """
    Generate substitution key dari keyword
    
    Args:
        keyword (str): Kata kunci
    
    Returns:
        dict: Substitution key
    """
    keyword = keyword.upper().replace(" ", "")
    
    # leungitkeun huruf duplikat
    seen = set()
    unique_keyword = []
    for char in keyword:
        if char not in seen and char.isalpha():
            seen.add(char)
            unique_keyword.append(char)
    
    # Tambahkeun sésa alfabet
    alphabet = string.ascii_uppercase
    substitution_alphabet = unique_keyword + [c for c in alphabet if c not in unique_keyword]
    
    return dict(zip(alphabet, substitution_alphabet))


def format_key_display(key):
    """
    Format key untuk ditampilkan dengan rapi
    
    Args:
        key (dict): Substitution key
    
    Returns:
        str: Key dalam format yang mudah dibaca
    """
    alphabet = string.ascii_uppercase
    cipher = ''.join(key[c] for c in alphabet)
    
    return f"Plain:  {alphabet}\nCipher: {cipher}"