import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

def _derive_key(password: str) -> bytes:
    """
    Derives a 32-byte AES key from the password using scrypt.
    Matches Node.js crypto.scryptSync defaults.
    """
    return hashlib.scrypt(
        password.encode('utf-8'),
        salt=b'salt',
        n=16384,
        r=8,
        p=1,
        dklen=32
    )

def encrypt_message(message: str, password: str) -> str:
    """
    Encrypts a message using AES-256-GCM.
    Returns format: iv_hex:auth_tag_hex:encrypted_hex
    """
    key = _derive_key(password)
    aesgcm = AESGCM(key)
    
    # Generate 16 byte IV (matching common Node.js practice for AES)
    iv = os.urandom(16)
    
    # Encrypt (cryptography's AESGCM appends the 16-byte auth tag to the ciphertext automatically)
    ciphertext_with_tag = aesgcm.encrypt(iv, message.encode('utf-8'), None)
    
    # Split ciphertext and tag
    ciphertext = ciphertext_with_tag[:-16]
    auth_tag = ciphertext_with_tag[-16:]
    
    return f"{iv.hex()}:{auth_tag.hex()}:{ciphertext.hex()}"

def decrypt_message(encrypted_payload: str, password: str) -> str:
    """
    Decrypts a message formatted as iv_hex:auth_tag_hex:encrypted_hex using AES-256-GCM.
    Raises ValueError if decryption fails (e.g., wrong password).
    """
    try:
        parts = encrypted_payload.split(':')
        if len(parts) != 3:
            raise ValueError("Invalid encrypted payload format")
            
        iv = bytes.fromhex(parts[0])
        auth_tag = bytes.fromhex(parts[1])
        ciphertext = bytes.fromhex(parts[2])
        
        key = _derive_key(password)
        aesgcm = AESGCM(key)
        
        # cryptography's AESGCM expects the tag appended to the ciphertext for decryption
        ciphertext_with_tag = ciphertext + auth_tag
        
        decrypted_bytes = aesgcm.decrypt(iv, ciphertext_with_tag, None)
        return decrypted_bytes.decode('utf-8')
        
    except (ValueError, InvalidTag):
        raise ValueError("Decryption failed. Invalid password or corrupted data.")
