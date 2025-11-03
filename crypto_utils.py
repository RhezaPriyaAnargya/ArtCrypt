import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from Crypto.Cipher import AES
from PIL import Image
import numpy as np
from io import BytesIO

MASTER_KEY = b'0123456789ABCDEF0123456789ABCDEF'  # 32 bytes

# === CORE CAMELIA FUNCTIONS ===
def camellia_encrypt_bytes(data):
    """Encrypt bytes using Camellia CBC → Base64"""
    iv = os.urandom(16)
    cipher = Cipher(algorithms.Camellia(MASTER_KEY), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # PKCS7 padding
    pad_len = 16 - (len(data) % 16)
    data += bytes([pad_len] * pad_len)
    
    encrypted = encryptor.update(data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted).decode()

def camellia_decrypt_bytes(encrypted_data):
    """Base64 decode → Camellia CBC decrypt → return bytes"""
    data = base64.b64decode(encrypted_data)
    iv, encrypted = data[:16], data[16:]
    
    cipher = Cipher(algorithms.Camellia(MASTER_KEY), modes.CBC(iv))
    decryptor = cipher.decryptor()
    
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    # Remove PKCS7 padding
    pad_len = decrypted[-1]
    return decrypted[:-pad_len]

# === USER AUTHENTICATION ===
def encrypt_username(username):
    """Username → Camellia CBC encrypt → Base64"""
    return camellia_encrypt_bytes(username.encode())

def encrypt_password(password):
    """Password → HMAC-SHA384 → Camellia CBC encrypt → Base64"""
    # HMAC-SHA384
    h = hmac.HMAC(MASTER_KEY, hashes.SHA384())
    h.update(password.encode())
    hash_pw = h.finalize()
    
    # Camellia CBC encrypt
    return camellia_encrypt_bytes(hash_pw)

def verify_user(input_user, input_pass, db_users):
    """Login: Base64 decode → Camellia decrypt → compare"""
    for user_id, user_enc, pass_enc in db_users:
        try:
            # Decrypt username
            decrypted_user = camellia_decrypt_bytes(user_enc).decode()
            
            if decrypted_user == input_user:
                # Verify password: HMAC input → compare with decrypted stored hash
                h = hmac.HMAC(MASTER_KEY, hashes.SHA384())
                h.update(input_pass.encode())
                hash_input = h.finalize()
                
                # Decrypt stored password hash
                decrypted_pass = camellia_decrypt_bytes(pass_enc)
                
                if hash_input == decrypted_pass:
                    return user_id
        except Exception:
            continue
    return None

# === METADATA ENCRYPTION ===
def caesar_encrypt(text, shift=3):
    """Caesar cipher encryption"""
    result = ""
    for char in text:
        if char.isalpha():
            base = 65 if char.isupper() else 97
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char  
    return result

def caesar_decrypt(text, shift=3):
    """Caesar cipher decryption"""
    return caesar_encrypt(text, -shift)

def aes_gcm_encrypt(data):
    """AES-128-GCM encryption → Base64"""
    if isinstance(data, str):
        data = data.encode()
    
    iv = os.urandom(12)
    cipher = AES.new(MASTER_KEY[:16], AES.MODE_GCM, nonce=iv)
    encrypted, tag = cipher.encrypt_and_digest(data)
    return base64.b64encode(iv + tag + encrypted).decode()

def aes_gcm_decrypt(encrypted_data):
    """Base64 decode → AES-128-GCM decryption → bytes"""
    data = base64.b64decode(encrypted_data)
    iv, tag, encrypted = data[:12], data[12:28], data[28:]
    cipher = AES.new(MASTER_KEY[:16], AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(encrypted, tag)

def encrypt_metadata(text):
    """Metadata: Caesar → AES-128-GCM → Camellia CBC → Base64"""
    # 1. Caesar Cipher
    caesar_text = caesar_encrypt(text)
    # 2. AES-128-GCM
    aes_encrypted = aes_gcm_encrypt(caesar_text)
    # 3. Camellia CBC
    return camellia_encrypt_bytes(aes_encrypted.encode())

def decrypt_metadata(encrypted_data):
    """Metadata: Base64 decode → Camellia CBC decrypt → AES-128-GCM decrypt → Caesar decrypt"""
    # 1. Camellia CBC decrypt
    camellia_decrypted = camellia_decrypt_bytes(encrypted_data).decode()
    # 2. AES-128-GCM decrypt
    aes_decrypted = aes_gcm_decrypt(camellia_decrypted)
    # 3. Caesar decrypt
    return caesar_decrypt(aes_decrypted.decode())

# === FILE ENCRYPTION (AES-CTR) ===
def aes_ctr_encrypt(data):
    """AES-128-CTR encryption → Base64"""
    # Nonce 8 bytes + Counter 8 bytes = 16 bytes total
    nonce = os.urandom(8)

    # Buat cipher AES-128-CTR
    # Format: nonce (8 bytes) akan digabung dengan counter (8 bytes) secara internal
    cipher = AES.new(MASTER_KEY[:16], AES.MODE_CTR, nonce=nonce)
    
    # Encrypt data (CTR mode tidak butuh padding)
    ciphertext = cipher.encrypt(data)
    
    return base64.b64encode(nonce + ciphertext).decode()

def aes_ctr_decrypt(encrypted_data):
    """Base64 decode → AES-CTR decryption → bytes"""
    data = base64.b64decode(encrypted_data)
    
    # Extract nonce (8 bytes) dan ciphertext
    nonce, ciphertext = data[:8], data[8:]
    
    # Buat cipher AES-CTR dengan nonce yang sama
    cipher = AES.new(MASTER_KEY[:16], AES.MODE_CTR, nonce=nonce)
    
    # Decrypt data
    return cipher.decrypt(ciphertext)

def encrypt_file(file_data):
    """File: AES-128-CTR → Camellia CBC → Base64"""
    # 1. AES-CTR encrypt
    aes_encrypted = aes_ctr_encrypt(file_data)
    # 2. Camellia CBC encrypt
    return camellia_encrypt_bytes(aes_encrypted.encode())

def decrypt_file(encrypted_data):
    """File: Base64 decode → Camellia CBC decrypt → AES-CTR decrypt"""
    # 1. Camellia CBC decrypt
    camellia_decrypted = camellia_decrypt_bytes(encrypted_data).decode()
    # 2. AES-CTR decrypt
    return aes_ctr_decrypt(camellia_decrypted)

# === TRUE BIT PLANE SLICING WATERMARKING ===
def embed_watermark_bitplane(image_file, watermark_text, bit_planes=[0, 1, 2]):
    """
    TRUE Bit Plane Slicing - Embed watermark in multiple bit planes
    bit_planes: list of bit positions (0-7) to use for embedding
    """
    img = Image.open(image_file).convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    
    # Convert watermark to binary
    watermark_bin = ''.join(format(ord(c), '08b') for c in watermark_text)
    watermark_bin += '00000000'  # Null terminator
    
    # Embed in selected bit planes
    flat = arr.flatten()
    watermark_index = 0
    
    for i in range(len(flat)):
        if watermark_index >= len(watermark_bin):
            break
            
        current_pixel = flat[i]
        
        for bit_pos in bit_planes:
            if watermark_index >= len(watermark_bin):
                break
                
            # Clear the target bit
            mask = 0xFF ^ (1 << bit_pos)
            current_pixel = current_pixel & mask
            
            # Set the bit from watermark
            bit_value = int(watermark_bin[watermark_index])
            current_pixel = current_pixel | (bit_value << bit_pos)
            watermark_index += 1
        
        flat[i] = current_pixel
    
    watermarked_arr = flat.reshape(arr.shape)
    watermarked_img = Image.fromarray(watermarked_arr)
    
    img_byte_arr = BytesIO()
    watermarked_img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def extract_watermark_bitplane(image_data, bit_planes=[0, 1, 2]):
    """
    Extract watermark from multiple bit planes
    bit_planes: list of bit positions (0-7) used for embedding
    """
    img = Image.open(BytesIO(image_data)).convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    
    flat = arr.flatten()
    binary_str = ''
    
    for pixel in flat:
        for bit_pos in bit_planes:
            bit_value = (pixel >> bit_pos) & 1
            binary_str += str(bit_value)
    
    # Convert binary to text
    chars = []
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if len(byte) < 8 or byte == '00000000':
            break
        chars.append(chr(int(byte, 2)))
    
    return ''.join(chars)

# === COMPATIBILITY FUNCTIONS ===
def embed_watermark(image_file, watermark_text):
    """Default watermark using LSB (bit plane 0) for compatibility"""
    return embed_watermark_bitplane(image_file, watermark_text, bit_planes=[0])

def extract_watermark_from_bytes(image_data, bit_planes=None):
    """Extraction with customizable bit planes"""
    if bit_planes is None:
        bit_planes = [0]  # Default to LSB for compatibility
    return extract_watermark_bitplane(image_data, bit_planes)