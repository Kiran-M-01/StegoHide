import io
from PIL import Image
from app.services.steganography import encode_image, decode_image

def test_steganography_modes():
    secret = "Hello Django! ASCII Payload Test 123 !@#$"
    
    print("--- Testing RGB Mode ---")
    img_rgb = Image.new('RGB', (100, 100), color='red')
    img_rgb_arr = io.BytesIO()
    img_rgb.save(img_rgb_arr, format='PNG')
    
    rgb_encoded = encode_image(img_rgb_arr.getvalue(), secret)
    rgb_decoded = decode_image(rgb_encoded)
    
    if rgb_decoded == secret:
        print("RGB test PASS")
    else:
        print(f"RGB test FAIL. Expected '{secret}', got '{rgb_decoded}'")
        
    print("\n--- Testing RGBA Mode ---")
    img_rgba = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img_rgba_arr = io.BytesIO()
    img_rgba.save(img_rgba_arr, format='PNG')
    
    rgba_encoded = encode_image(img_rgba_arr.getvalue(), secret)
    rgba_decoded = decode_image(rgba_encoded)
    
    if rgba_decoded == secret:
        print("RGBA test PASS")
    else:
        print(f"RGBA test FAIL. Expected '{secret}', got '{rgba_decoded}'")

if __name__ == "__main__":
    test_steganography_modes()
