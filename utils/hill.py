import numpy as np

def text_to_numbers(text):
    """
    Konversi teks ke array angka (A=0, B=1, ..., Z=25)
    
    Args:
        text (str): Teks input
    
    Returns:
        list: List angka
    """
    text = text.upper()
    return [ord(char) - ord('A') for char in text if char.isalpha()]


def numbers_to_text(numbers):
    """
    Konversi array angka ke teks
    
    Args:
        numbers (list): List angka
    
    Returns:
        str: Teks hasil konversi
    """
    return ''.join(chr(num % 26 + ord('A')) for num in numbers)


def matrix_mod_inv(matrix, modulus=26):
    """
    Hitung inverse matriks dalam modulo
    
    Args:
        matrix (numpy.ndarray): Matriks input
        modulus (int): Nilai modulo
    
    Returns:
        numpy.ndarray: Inverse matriks atau None jika tidak ada
    """
    det = int(round(np.linalg.det(matrix)))
    det_inv = mod_inverse(det % modulus, modulus)
    
    if det_inv is None:
        return None
    
    matrix_inv = det_inv * np.round(det * np.linalg.inv(matrix)).astype(int)
    return matrix_inv % modulus


def mod_inverse(a, m):
    """
    Hitung modular multiplicative inverse
    
    Args:
        a (int): Angka
        m (int): Modulo
    
    Returns:
        int: Inverse atau None jika tidak ada
    """
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    
    gcd, x, _ = extended_gcd(a % m, m)
    
    if gcd != 1:
        return None
    return (x % m + m) % m


def generate_key_matrix(key, size=2):
    """
    Generate key matrix dari string atau list
    
    Args:
        key (str or list): Key sebagai string atau list angka
        size (int): Ukuran matriks (2 atau 3)
    
    Returns:
        numpy.ndarray: Key matrix
    """
    if isinstance(key, str):
        key = key.upper().replace(' ', '')
        key_numbers = text_to_numbers(key)
    else:
        key_numbers = key
    
    # pastikeun panjang konci sesuai ukuran matriks na
    needed = size * size
    if len(key_numbers) < needed:
        # pad ku nol
        key_numbers += [0] * (needed - len(key_numbers))
    elif len(key_numbers) > needed:
        key_numbers = key_numbers[:needed]
    
    matrix = np.array(key_numbers).reshape(size, size)
    return matrix


def hill_encrypt(plaintext, key_matrix):
    """
    Enkripsi menggunakan Hill Cipher
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        key_matrix (numpy.ndarray): Matriks kunci
    
    Returns:
        str: Teks terenkripsi
    """
    size = key_matrix.shape[0]
    numbers = text_to_numbers(plaintext)
    
    # pad teks supaya panjangna kelipatan size
    while len(numbers) % size != 0:
        numbers.append(23)  # pad ku 'X' (23)
    
    encrypted = []
    
    # Enkripsi per blok
    for i in range(0, len(numbers), size):
        block = np.array(numbers[i:i+size])
        encrypted_block = np.dot(key_matrix, block) % 26
        encrypted.extend(encrypted_block.tolist())
    
    return numbers_to_text(encrypted)


def hill_decrypt(ciphertext, key_matrix):
    """
    Dekripsi Hill Cipher
    
    Args:
        ciphertext (str): Teks terenkripsi
        key_matrix (numpy.ndarray): Matriks kunci
    
    Returns:
        str or None: Teks asli atau None jika dekripsi gagal
    """
    # hitung inverse matriks konci
    inv_key_matrix = matrix_mod_inv(key_matrix)
    
    if inv_key_matrix is None:
        return None
    
    size = key_matrix.shape[0]
    numbers = text_to_numbers(ciphertext)
    
    decrypted = []
    
    # Dekripsi tiap blok
    for i in range(0, len(numbers), size):
        block = np.array(numbers[i:i+size])
        decrypted_block = np.dot(inv_key_matrix, block) % 26
        decrypted.extend(decrypted_block.tolist())
    
    return numbers_to_text(decrypted)


def is_valid_key_matrix(matrix):
    """
    Validasi apakah matriks bisa digunakan sebagai key
    (determinan harus coprime dengan 26)
    
    Args:
        matrix (numpy.ndarray): Matriks yang akan divalidasi
    
    Returns:
        tuple: (valid, message)
    """
    try:
        det = int(round(np.linalg.det(matrix))) % 26
        
        if det == 0:
            return False, "Determinan adalah 0, matriks tidak invertible"
        
        inv = mod_inverse(det, 26)
        if inv is None:
            return False, f"Determinan {det} tidak coprime dengan 26"
        
        return True, "Matriks valid"
    except Exception as e:
        return False, f"Error: {str(e)}"


def create_example_key(size=2):
    """
    Buat contoh key matrix yang valid
    
    Args:
        size (int): Ukuran matriks
    
    Returns:
        numpy.ndarray: Key matrix contoh
    """
    if size == 2:
        # conto konci 2x2
        return np.array([[7, 8], [11, 11]])
    elif size == 3:
        # Conto konci 3x3
        return np.array([[6, 24, 1], [13, 16, 10], [20, 17, 15]])
    else:
        return np.eye(size, dtype=int)