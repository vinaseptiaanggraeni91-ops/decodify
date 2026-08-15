import random
import math

def is_prime(n, k=5):
    """
    Test apakah n adalah bilangan prima menggunakan Miller-Rabin
    
    Args:
        n (int): Angka yang akan ditest
        k (int): Jumlah iterasi test
    
    Returns:
        bool: True jika kemungkinan prima
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # tulis n-1 sapertos 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    # laksanakeun k iterasi test
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True


def generate_prime(bits=16):
    """
    Generate bilangan prima random
    
    Args:
        bits (int): Jumlah bit untuk prima
    
    Returns:
        int: Bilangan prima
    """
    while True:
        n = random.getrandbits(bits)
        n |= (1 << bits - 1) | 1  # pastikeun bit paling luhur jeung paling handap diset
        if is_prime(n):
            return n


def gcd(a, b):
    """
    Hitung Greatest Common Divisor
    
    Args:
        a (int): Angka pertama
        b (int): Angka kedua
    
    Returns:
        int: GCD dari a dan b
    """
    while b:
        a, b = b, a % b
    return a


def mod_inverse(e, phi):
    """
    Hitung modular multiplicative inverse menggunakan Extended Euclidean
    
    Args:
        e (int): Angka
        phi (int): Modulo
    
    Returns:
        int: Inverse dari e mod phi
    """
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd_val, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd_val, x, y
    
    gcd_val, x, _ = extended_gcd(e % phi, phi)
    if gcd_val != 1:
        raise Exception('Modular inverse tidak ada')
    return (x % phi + phi) % phi


def generate_keypair(bits=16):
    """
    Generate pasangan public dan private key RSA
    
    Args:
        bits (int): Ukuran bit untuk prima (default 16 untuk demo)
    
    Returns:
        tuple: ((e, n), (d, n)) - public key, private key
    """
    # Generate dua bilangan prima
    p = generate_prime(bits)
    q = generate_prime(bits)
    
    # itung n jeung phi
    n = p * q
    phi = (p - 1) * (q - 1)
    
    # Pilih e (public key exponent)
    e = random.randrange(2, phi)
    while gcd(e, phi) != 1:
        e = random.randrange(2, phi)
    
    # itung d (private key exponent)
    d = mod_inverse(e, phi)
    
    return ((e, n), (d, n))


def rsa_encrypt(message, public_key):
    """
    Enkripsi pesan menggunakan RSA
    
    Args:
        message (str): Pesan yang akan dienkripsi
        public_key (tuple): (e, n)
    
    Returns:
        list: List angka terenkripsi
    """
    e, n = public_key
    
    # konversi unggal karakter jadi angka terénkripsi
    encrypted = []
    for char in message:
        m = ord(char)
        # Enkripsi: c = m^e mod n
        c = pow(m, e, n)
        encrypted.append(c)
    
    return encrypted


def rsa_decrypt(ciphertext, private_key):
    """
    Dekripsi pesan RSA
    
    Args:
        ciphertext (list): List angka terenkripsi
        private_key (tuple): (d, n)
    
    Returns:
        str: Pesan asli
    """
    d, n = private_key
    
    # konversi unggal angka deui jadi karakter asli
    decrypted = []
    for c in ciphertext:
        # Dekripsi: m = c^d mod n
        m = pow(c, d, n)
        decrypted.append(chr(m))
    
    return ''.join(decrypted)


def rsa_encrypt_number(number, public_key):
    """
    Enkripsi satu angka dengan RSA
    
    Args:
        number (int): Angka yang akan dienkripsi
        public_key (tuple): (e, n)
    
    Returns:
        int: Angka terenkripsi
    """
    e, n = public_key
    return pow(number, e, n)


def rsa_decrypt_number(ciphertext, private_key):
    """
    Dekripsi satu angka RSA
    
    Args:
        ciphertext (int): Angka terenkripsi
        private_key (tuple): (d, n)
    
    Returns:
        int: Angka asli
    """
    d, n = private_key
    return pow(ciphertext, d, n)


def format_key(key):
    """
    Format key untuk ditampilkan
    
    Args:
        key (tuple): (exponent, modulus)
    
    Returns:
        str: Key dalam format string
    """
    exp, mod = key
    return f"Exponent: {exp}\nModulus: {mod}"


def ciphertext_to_string(ciphertext):
    """
    Konversi list ciphertext ke string untuk ditampilkan
    
    Args:
        ciphertext (list): List angka terenkripsi
    
    Returns:
        str: String representation
    """
    return ' '.join(map(str, ciphertext))


def string_to_ciphertext(cipher_string):
    """
    Konversi string kembali ke list ciphertext
    
    Args:
        cipher_string (str): String angka-angka
    
    Returns:
        list: List angka
    """
    return [int(x) for x in cipher_string.split()]