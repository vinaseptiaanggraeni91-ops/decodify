import math

def rail_fence_encrypt(plaintext, rails):
    """
    Enkripsi menggunakan Rail Fence Cipher (Zigzag)
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        rails (int): Jumlah rail/baris (min 2)
    
    Returns:
        str: Teks terenkripsi
    """
    if rails < 2:
        return plaintext
    
    # jieun matrix rail
    fence = [[] for _ in range(rails)]
    rail = 0
    direction = 1  # 1 keur turun, -1 keur naek
    
    # Eserkeun karakter kana rail sesuai pola zigzag
    for char in plaintext:
        fence[rail].append(char)
        rail += direction
        
        # Balikeun arah lamun ngahontal rail paling luhur atawa paling handap
        if rail == 0 or rail == rails - 1:
            direction *= -1
    
    # Gabungkan semua baris
    return ''.join([''.join(row) for row in fence])


def rail_fence_decrypt(ciphertext, rails):
    """
    Dekripsi Rail Fence Cipher
    
    Args:
        ciphertext (str): Teks terenkripsi
        rails (int): Jumlah rail yang digunakan
    
    Returns:
        str: Teks asli
    """
    if rails < 2:
        return ciphertext
    
    # tangtukeun panyang tiap rail
    fence_lengths = [0] * rails
    rail = 0
    direction = 1
    
    for _ in ciphertext:
        fence_lengths[rail] += 1
        rail += direction
        if rail == 0 or rail == rails - 1:
            direction *= -1
    
    # pisahkeun ciphertext kana rail
    fence = []
    pos = 0
    for length in fence_lengths:
        fence.append(list(ciphertext[pos:pos + length]))
        pos += length
    
    # baca deui ciphertext nurutkeun pola zigzag
    result = []
    rail = 0
    direction = 1
    
    for _ in ciphertext:
        result.append(fence[rail].pop(0))
        rail += direction
        if rail == 0 or rail == rails - 1:
            direction *= -1
    
    return ''.join(result)


def columnar_transposition_encrypt(plaintext, key):
    """
    Enkripsi menggunakan Columnar Transposition
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        key (str): Kata kunci untuk menentukan urutan kolom
    
    Returns:
        str: Teks terenkripsi
    """
    # Lengitkeun spasi dina key
    key = key.replace(" ", "")
    key_length = len(key)
    
    # Urutkeun konci pikeun menentukan urutan pembacaan
    sorted_key = sorted(enumerate(key), key=lambda x: x[1])
    column_order = [i for i, _ in sorted_key]
    
    # Jieun kotak-kotak kosong
    num_rows = math.ceil(len(plaintext) / key_length)
    grid = [''] * key_length
    
    # Eusi kotak-kotak per kolom
    for i, char in enumerate(plaintext):
        col = i % key_length
        grid[col] += char
    
    # baca kotak-kotak nurutkeun urutan kolom
    ciphertext = ''
    for col in column_order:
        ciphertext += grid[col]
    
    return ciphertext


def columnar_transposition_decrypt(ciphertext, key):
    """
    Dekripsi Columnar Transposition
    
    Args:
        ciphertext (str): Teks terenkripsi
        key (str): Kata kunci yang digunakan
    
    Returns:
        str: Teks asli
    """
    key = key.replace(" ", "")
    key_length = len(key)
    
    # Urutkeun konci pikeun menentukan urutan bacaeun
    sorted_key = sorted(enumerate(key), key=lambda x: x[1])
    column_order = [i for i, _ in sorted_key]
    
    # itung jumlah baris
    num_rows = math.ceil(len(ciphertext) / key_length)
    num_full_cols = len(ciphertext) % key_length
    if num_full_cols == 0:
        num_full_cols = key_length
    
    # jieun kotak-kotak kosong
    grid = [''] * key_length
    
    # eusi kotak-kotak per kolom nurutkeun urutan konci
    pos = 0
    for col in column_order:
        col_length = num_rows if col < num_full_cols else num_rows - 1
        grid[col] = ciphertext[pos:pos + col_length]
        pos += col_length
    
    # baca kotak-kotak per baris
    plaintext = ''
    for row in range(num_rows):
        for col in range(key_length):
            if row < len(grid[col]):
                plaintext += grid[col][row]
    
    return plaintext


def route_cipher_encrypt(plaintext, rows, cols):
    """
    Enkripsi menggunakan Route Cipher (spiral/snake pattern)
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        rows (int): Jumlah baris
        cols (int): Jumlah kolom
    
    Returns:
        str: Teks terenkripsi
    """
    # pad teks lamun perlu
    total_cells = rows * cols
    padded_text = plaintext + 'X' * (total_cells - len(plaintext))
    
    # jieun kotak-kotak per baris
    grid = []
    pos = 0
    for _ in range(rows):
        row = []
        for _ in range(cols):
            row.append(padded_text[pos] if pos < len(padded_text) else 'X')
            pos += 1
        grid.append(row)
    
    # baca per kolom
    ciphertext = ''
    for col in range(cols):
        for row in range(rows):
            ciphertext += grid[row][col]
    
    return ciphertext


def route_cipher_decrypt(ciphertext, rows, cols):
    """
    Dekripsi Route Cipher
    
    Args:
        ciphertext (str): Teks terenkripsi
        rows (int): Jumlah baris yang digunakan
        cols (int): Jumlah kolom yang digunakan
    
    Returns:
        str: Teks asli
    """
    # jieun kotak-kotak kosong terus eusi per kolom
    grid = [['' for _ in range(cols)] for _ in range(rows)]
    pos = 0
    
    for col in range(cols):
        for row in range(rows):
            if pos < len(ciphertext):
                grid[row][col] = ciphertext[pos]
                pos += 1
    
    # Baca per baris
    plaintext = ''
    for row in range(rows):
        for col in range(cols):
            plaintext += grid[row][col]
    
    return plaintext.rstrip('X')