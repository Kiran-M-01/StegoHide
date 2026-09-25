from PIL import Image
import io
import os
from app.services.steganography import encode_image, decode_image

def test_steganography():
    # 1. Create a dummy image in memory
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    original_bytes = img_byte_arr.getvalue()
    
    # 2. Secret message
    secret = "Hello Django! This is a secret test."
    print(f"Original message: '{secret}'")
    
    # 3. Encode
    encoded_bytes = encode_image(original_bytes, secret)
    print(f"Image encoded successfully. Original size: {len(original_bytes)}, Encoded size: {len(encoded_bytes)}")
    
    # 4. Decode
    decoded_message = decode_image(encoded_bytes)
    print(f"Decoded message: '{decoded_message}'")
    
    if secret == decoded_message:
        print("SUCCESS! The LSB steganography works perfectly.")
    else:
        print("ERROR! Decoded message does not match.")

if __name__ == "__main__":
    test_steganography()
