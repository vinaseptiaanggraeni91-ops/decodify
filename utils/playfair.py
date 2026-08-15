import string

def generate_playfair_matrix(key):
    """
    Generate matriks 5x5 Playfair dari keyword
    I dan J digabung menjadi satu
    
    Args:
        key (str): Kata kunci
    
    Returns:
        list: Matriks 5x5
    """
    # bersihkeun konci tina spasi jeung ganti J jadi I
    key = key.upper().replace('J', 'I').replace(' ', '')
    
    # jieun salinan huruf unik tina konci
    alphabet = ""
    seen = set()
    
    for char in key:
        if char.isalpha() and char not in seen:
            alphabet += char
            seen.add(char)
    
    # tambahan sesa huruf alfabet
    for char in string.ascii_uppercase:
        if char not in seen and char != 'J':
            alphabet += char
            seen.add(char)
    
    # jieunkeun matriks 5x5
    matrix = []
    for i in range(5):
        row = []
        for j in range(5):
            row.append(alphabet[i * 5 + j])
        matrix.append(row)
    
    return matrix


def find_position(matrix, char):
    """
    Cari posisi karakter dalam matriks
    
    Args:
        matrix (list): Matriks Playfair
        char (str): Karakter yang dicari
    
    Returns:
        tuple: (row, col)
    """
    for i in range(5):
        for j in range(5):
            if matrix[i][j] == char:
                return (i, j)
    return None


def prepare_text(text):
    """
    Persiapkan teks untuk enkripsi Playfair
    - Ubah J menjadi I
    - Pisahkan huruf kembar dengan X
    - Tambahkan X di akhir jika panjang ganjil
    
    Args:
        text (str): Teks asli
    
    Returns:
        str: Teks yang sudah diproses
    """
    text = text.upper().replace('J', 'I')
    # cokot ngan karakter alfabet hungkul
    text = ''.join(c for c in text if c.isalpha())
    
    # pisah huruf kembar jeung tambahkeun X
    prepared = ""
    i = 0
    while i < len(text):
        prepared += text[i]
        
        if i + 1 < len(text):
            if text[i] == text[i + 1]:
                prepared += 'X'
            else:
                prepared += text[i + 1]
                i += 1
        i += 1
    
    # tambahkeun X lamun panjang ganjil
    if len(prepared) % 2 != 0:
        prepared += 'X'
    
    return prepared


def playfair_encrypt(plaintext, key):
    """
    Enkripsi menggunakan Playfair Cipher
    
    Args:
        plaintext (str): Teks yang akan dienkripsi
        key (str): Kata kunci
    
    Returns:
        str: Teks terenkripsi
    """
    matrix = generate_playfair_matrix(key)
    prepared = prepare_text(plaintext)
    
    ciphertext = ""
    
    # Proses per pasangan huruf
    for i in range(0, len(prepared), 2):
        char1 = prepared[i]
        char2 = prepared[i + 1]
        
        row1, col1 = find_position(matrix, char1)
        row2, col2 = find_position(matrix, char2)
        
        # Aturan ka 1: Baris sarua
        if row1 == row2:
            ciphertext += matrix[row1][(col1 + 1) % 5]
            ciphertext += matrix[row2][(col2 + 1) % 5]
        
        # Aturan ka 2: Kolom sarua
        elif col1 == col2:
            ciphertext += matrix[(row1 + 1) % 5][col1]
            ciphertext += matrix[(row2 + 1) % 5][col2]
        
        # Aturan ka 3: Bentuk persegi
        else:
            ciphertext += matrix[row1][col2]
            ciphertext += matrix[row2][col1]
    
    return ciphertext


def playfair_decrypt(ciphertext, key):
    """
    Dekripsi Playfair Cipher
    
    Args:
        ciphertext (str): Teks terenkripsi
        key (str): Kata kunci
    
    Returns:
        str: Teks asli
    """
    matrix = generate_playfair_matrix(key)
    ciphertext = ciphertext.upper().replace(' ', '')
    
    plaintext = ""
    
    # Proses per pasangan huruf
    for i in range(0, len(ciphertext), 2):
        if i + 1 >= len(ciphertext):
            break
            
        char1 = ciphertext[i]
        char2 = ciphertext[i + 1]
        
        row1, col1 = find_position(matrix, char1)
        row2, col2 = find_position(matrix, char2)
        
        if row1 is None or row2 is None:
            continue
        
        # Aturan ka 1: Baris sarua (esérkeun ka kénca)
        if row1 == row2:
            plaintext += matrix[row1][(col1 - 1) % 5]
            plaintext += matrix[row2][(col2 - 1) % 5]
        
        # Aturan ka 2: Kolom sarua (esérkeun ka luhur)
        elif col1 == col2:
            plaintext += matrix[(row1 - 1) % 5][col1]
            plaintext += matrix[(row2 - 1) % 5][col2]
        
        # Aturan ka 3: Bentukeun persegi
        else:
            plaintext += matrix[row1][col2]
            plaintext += matrix[row2][col1]
    
    return plaintext

# nambahkeun fungsi pikeun nembongkeun matriks Playfair
def display_playfair_matrix(key):
    """
    Tampilkan matriks Playfair dalam format yang rapi
    
    Args:
        key (str): Kata kunci
    
    Returns:
        str: Matriks dalam string
    """
    matrix = generate_playfair_matrix(key)
    result = "Playfair Matrix (5x5):\n"
    result += "─" * 21 + "\n"
    
    for row in matrix:
        result += "│ " + " ".join(row) + " │\n"
    
    result += "─" * 21
    return result