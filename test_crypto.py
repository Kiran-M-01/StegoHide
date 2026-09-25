from app.services.encryption import encrypt_message, decrypt_message

def test_encryption():
    message = "Super Secret Password 123"
    password = "MySecurePassword"
    
    print(f"Original message: {message}")
    
    # Encrypt
    encrypted_payload = encrypt_message(message, password)
    print(f"Encrypted payload: {encrypted_payload}")
    
    # Decrypt
    decrypted = decrypt_message(encrypted_payload, password)
    print(f"Decrypted message: {decrypted}")
    
    if message == decrypted:
        print("SUCCESS! Encryption/Decryption round trip works.")
    else:
        print("ERROR! Messages do not match.")
        
    # Test wrong password
    try:
        decrypt_message(encrypted_payload, "WrongPassword")
        print("ERROR! Decryption succeeded with wrong password.")
    except ValueError as e:
        print(f"SUCCESS! Caught expected error with wrong password: {e}")

if __name__ == "__main__":
    test_encryption()
