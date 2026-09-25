import io
from PIL import Image

def encode_image(image_bytes: bytes, message: str) -> bytes:
    """
    Encode a message into an image using LSB steganography.
    Matches the original Node.js Sharp implementation exactly.
    """
    # 1. Convert the message to UTF-8 bytes before converting to bits
    msg_bytes = (message + '\0').encode('utf-8')
    
    bits = []
    for b in msg_bytes:
        for bit in format(b, '08b'):
            bits.append(int(bit))
            
    message_len = len(bits)
    
    # Open image using Pillow
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
    
    # Get raw pixel data as a mutable bytearray
    pixel_data = bytearray(img.tobytes())
    
    if message_len > len(pixel_data):
        raise ValueError("Image is too small to hold the message")
    
    for i in range(message_len):
        # 2. Do NOT skip the alpha channel.
        # 3. Preserve the original raw-byte LSB algorithm:
        pixel_data[i] = (pixel_data[i] & 0xFE) | bits[i]
            
    # Create a new image from the modified pixel data
    encoded_img = Image.frombytes(img.mode, img.size, bytes(pixel_data))
    
    # 6. Preserve PNG output
    output_buffer = io.BytesIO()
    encoded_img.save(output_buffer, format="PNG")
    return output_buffer.getvalue()


def decode_image(image_bytes: bytes) -> str:
    """
    Decode a message from an image using LSB steganography.
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
        
    pixel_data = img.tobytes()
    
    msg_bytes = bytearray()
    current_byte = 0
    bit_count = 0
    
    for i in range(len(pixel_data)):
        # Extract the LSB
        bit = pixel_data[i] & 1
        current_byte = (current_byte << 1) | bit
        bit_count += 1
        
        # Check if we have formed a complete byte
        if bit_count == 8:
            msg_bytes.append(current_byte)
            if current_byte == 0:
                break
            current_byte = 0
            bit_count = 0
                
    # 5. Make the decode implementation recover the same byte sequence
    #    produced by the original algorithm and stop at the null terminator.
    if len(msg_bytes) > 0 and msg_bytes[-1] == 0:
        msg_bytes = msg_bytes[:-1]
        
    return msg_bytes.decode('utf-8')
