"""
Modern Cryptography Utilities
Fitur Premium: AES, DES, 3DES, Blowfish
"""

from Crypto.Cipher import AES, DES, DES3, Blowfish
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import hashlib

def validate_key_length(key, required_length, algorithm_name):
    """Validasi panjang key untuk algoritma tertentu"""
    if len(key) < required_length:
        raise ValueError(f'{algorithm_name} memerlukan key minimal {required_length} karakter')
    return key[:required_length].encode('utf-8')

def aes_encrypt(plaintext, key):
    """
    AES Encryption (Advanced Encryption Standard)
    - Key length: 16, 24, atau 32 bytes (128, 192, 256 bit)
    - Block size: 16 bytes
    - Mode: CBC (Cipher Block Chaining)
    """
    # Pastikan key length 16, 24, atau 32 bytes
    if len(key) < 16:
        key = key.ljust(16, '0')
    elif len(key) < 24:
        key = key[:16]
    elif len(key) < 32:
        key = key[:24]
    else:
        key = key[:32]
    
    key_bytes = key.encode('utf-8')
    
    # Generate random IV (Initialization Vector)
    iv = get_random_bytes(AES.block_size)
    
    # Create cipher object
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    
    # Pad plaintext dan encrypt
    padded_text = pad(plaintext.encode('utf-8'), AES.block_size)
    ciphertext = cipher.encrypt(padded_text)
    
    # Encode ke base64 biar bisa ditampilkan
    return base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(iv).decode('utf-8')

def aes_decrypt(ciphertext, key, iv):
    """AES Decryption"""
    # Pastikan key length sama dengan saat encrypt
    if len(key) < 16:
        key = key.ljust(16, '0')
    elif len(key) < 24:
        key = key[:16]
    elif len(key) < 32:
        key = key[:24]
    else:
        key = key[:32]
    
    key_bytes = key.encode('utf-8')
    
    # Decode dari base64
    ciphertext_bytes = base64.b64decode(ciphertext)
    iv_bytes = base64.b64decode(iv)
    
    # Create cipher object
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    
    # Decrypt dan unpad
    decrypted = cipher.decrypt(ciphertext_bytes)
    plaintext = unpad(decrypted, AES.block_size)
    
    return plaintext.decode('utf-8')

def des_encrypt(plaintext, key):
    """
    DES Encryption (Data Encryption Standard)
    - Key length: 8 bytes (64 bit, efektif 56 bit)
    - Block size: 8 bytes
    - Mode: CBC
    - Note: DES sudah tidak aman, gunakan untuk pembelajaran saja
    """
    # DES butuh key 8 bytes
    if len(key) < 8:
        key = key.ljust(8, '0')
    else:
        key = key[:8]
    
    key_bytes = key.encode('utf-8')
    
    # Generate random IV
    iv = get_random_bytes(DES.block_size)
    
    # Create cipher object
    cipher = DES.new(key_bytes, DES.MODE_CBC, iv)
    
    # Pad dan encrypt
    padded_text = pad(plaintext.encode('utf-8'), DES.block_size)
    ciphertext = cipher.encrypt(padded_text)
    
    return base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(iv).decode('utf-8')

def des_decrypt(ciphertext, key, iv):
    """DES Decryption"""
    # DES butuh key 8 bytes
    if len(key) < 8:
        key = key.ljust(8, '0')
    else:
        key = key[:8]
    
    key_bytes = key.encode('utf-8')
    
    # Decode dari base64
    ciphertext_bytes = base64.b64decode(ciphertext)
    iv_bytes = base64.b64decode(iv)
    
    # Create cipher object
    cipher = DES.new(key_bytes, DES.MODE_CBC, iv_bytes)
    
    # Decrypt dan unpad
    decrypted = cipher.decrypt(ciphertext_bytes)
    plaintext = unpad(decrypted, DES.block_size)
    
    return plaintext.decode('utf-8')

def triple_des_encrypt(plaintext, key):
    """
    3DES Encryption (Triple DES)
    - Key length: 16 atau 24 bytes (128 atau 192 bit)
    - Block size: 8 bytes
    - Mode: CBC
    - 3x lebih aman dari DES
    """
    # 3DES butuh key 16 atau 24 bytes
    if len(key) < 16:
        key = key.ljust(16, '0')
    elif len(key) > 24:
        key = key[:24]
    else:
        # Adjust ke 16 atau 24
        if len(key) < 24:
            key = key[:16]
    
    key_bytes = key.encode('utf-8')
    
    # Generate random IV
    iv = get_random_bytes(DES3.block_size)
    
    # Create cipher object
    cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv)
    
    # Pad dan encrypt
    padded_text = pad(plaintext.encode('utf-8'), DES3.block_size)
    ciphertext = cipher.encrypt(padded_text)
    
    return base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(iv).decode('utf-8')

def triple_des_decrypt(ciphertext, key, iv):
    """3DES Decryption"""
    # 3DES butuh key 16 atau 24 bytes
    if len(key) < 16:
        key = key.ljust(16, '0')
    elif len(key) > 24:
        key = key[:24]
    else:
        if len(key) < 24:
            key = key[:16]
    
    key_bytes = key.encode('utf-8')
    
    # Decode dari base64
    ciphertext_bytes = base64.b64decode(ciphertext)
    iv_bytes = base64.b64decode(iv)
    
    # Create cipher object
    cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv_bytes)
    
    # Decrypt dan unpad
    decrypted = cipher.decrypt(ciphertext_bytes)
    plaintext = unpad(decrypted, DES3.block_size)
    
    return plaintext.decode('utf-8')

def blowfish_encrypt(plaintext, key):
    """
    Blowfish Encryption
    - Key length: 4 sampai 56 bytes (32-448 bit)
    - Block size: 8 bytes
    - Mode: CBC
    - Cepat dan aman untuk data kecil
    """
    # Blowfish flexible, tapi minimal 4 bytes
    if len(key) < 4:
        key = key.ljust(4, '0')
    elif len(key) > 56:
        key = key[:56]
    
    key_bytes = key.encode('utf-8')
    
    # Generate random IV
    iv = get_random_bytes(Blowfish.block_size)
    
    # Create cipher object
    cipher = Blowfish.new(key_bytes, Blowfish.MODE_CBC, iv)
    
    # Pad dan encrypt
    padded_text = pad(plaintext.encode('utf-8'), Blowfish.block_size)
    ciphertext = cipher.encrypt(padded_text)
    
    return base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(iv).decode('utf-8')

def blowfish_decrypt(ciphertext, key, iv):
    """Blowfish Decryption"""
    # Blowfish flexible
    if len(key) < 4:
        key = key.ljust(4, '0')
    elif len(key) > 56:
        key = key[:56]
    
    key_bytes = key.encode('utf-8')
    
    # Decode dari base64
    ciphertext_bytes = base64.b64decode(ciphertext)
    iv_bytes = base64.b64decode(iv)
    
    # Create cipher object
    cipher = Blowfish.new(key_bytes, Blowfish.MODE_CBC, iv_bytes)
    
    # Decrypt dan unpad
    decrypted = cipher.decrypt(ciphertext_bytes)
    plaintext = unpad(decrypted, Blowfish.block_size)
    
    return plaintext.decode('utf-8')

# Utility functions
def get_algorithm_info():
    """Informasi tentang algoritma modern"""
    return {
        'AES': {
            'name': 'Advanced Encryption Standard',
            'key_size': '128, 192, atau 256 bit',
            'block_size': '128 bit',
            'status': 'Standar industri - Sangat Aman',
            'use_case': 'Enkripsi file, komunikasi, database'
        },
        'DES': {
            'name': 'Data Encryption Standard',
            'key_size': '56 bit (efektif)',
            'block_size': '64 bit',
            'status': 'Deprecated - Tidak Aman',
            'use_case': 'Hanya untuk pembelajaran'
        },
        '3DES': {
            'name': 'Triple DES',
            'key_size': '112 atau 168 bit',
            'block_size': '64 bit',
            'status': 'Legacy - Kurang Efisien',
            'use_case': 'Sistem lama yang belum migrasi ke AES'
        },
        'Blowfish': {
            'name': 'Blowfish',
            'key_size': '32-448 bit',
            'block_size': '64 bit',
            'status': 'Masih Aman - Tapi Lebih Lambat dari AES',
            'use_case': 'Enkripsi password, data kecil'
        }
    }

if __name__ == '__main__':
    # Test
    text = "Hello World 123!"
    key = "mysecretkey12345"
    
    print("=== AES Test ===")
    encrypted, iv = aes_encrypt(text, key)
    print(f"Encrypted: {encrypted}")
    print(f"IV: {iv}")
    decrypted = aes_decrypt(encrypted, key, iv)
    print(f"Decrypted: {decrypted}")
    
    print("\n=== DES Test ===")
    encrypted, iv = des_encrypt(text, key)
    print(f"Encrypted: {encrypted}")
    decrypted = des_decrypt(encrypted, key, iv)
    print(f"Decrypted: {decrypted}")