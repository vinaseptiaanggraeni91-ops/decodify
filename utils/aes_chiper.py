from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

def aes_encrypt(plaintext, key):
    """
    Enkripsi menggunakan AES-256-CBC
    
    Args:
        plaintext (str): Text yang akan dienkripsi
        key (str): Encryption key (16-32 karakter)
    
    Returns:
        tuple: (ciphertext_base64, iv_base64)
    """
    # Adjust key length to 16, 24, or 32 bytes
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 16:
        raise ValueError("Key harus minimal 16 karakter")
    elif len(key_bytes) < 24:
        key_bytes = key_bytes[:16].ljust(16, b'\0')
    elif len(key_bytes) < 32:
        key_bytes = key_bytes[:24].ljust(24, b'\0')
    else:
        key_bytes = key_bytes[:32]
    
    # Generate random IV
    iv = get_random_bytes(16)
    
    # Create cipher
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    
    # Encrypt
    plaintext_bytes = plaintext.encode('utf-8')
    padded_plaintext = pad(plaintext_bytes, AES.block_size)
    ciphertext = cipher.encrypt(padded_plaintext)
    
    # Return as base64
    ciphertext_base64 = base64.b64encode(ciphertext).decode('utf-8')
    iv_base64 = base64.b64encode(iv).decode('utf-8')
    
    return ciphertext_base64, iv_base64


def aes_decrypt(ciphertext_base64, key, iv_base64):
    """
    Dekripsi AES-256-CBC
    
    Args:
        ciphertext_base64 (str): Ciphertext dalam base64
        key (str): Encryption key (sama seperti saat enkripsi)
        iv_base64 (str): IV dalam base64
    
    Returns:
        str: Plaintext
    """
    # Adjust key length
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 16:
        raise ValueError("Key harus minimal 16 karakter")
    elif len(key_bytes) < 24:
        key_bytes = key_bytes[:16].ljust(16, b'\0')
    elif len(key_bytes) < 32:
        key_bytes = key_bytes[:24].ljust(24, b'\0')
    else:
        key_bytes = key_bytes[:32]
    
    # Decode from base64
    ciphertext = base64.b64decode(ciphertext_base64)
    iv = base64.b64decode(iv_base64)
    
    # Create cipher
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    
    # Decrypt
    padded_plaintext = cipher.decrypt(ciphertext)
    plaintext_bytes = unpad(padded_plaintext, AES.block_size)
    
    return plaintext_bytes.decode('utf-8')