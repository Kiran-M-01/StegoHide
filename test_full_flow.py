import os
import django
import io
import json
from unittest.mock import patch
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from django.core.cache import cache
from app.models import Encode

@patch('app.views.send_otp_email', return_value=True)
@patch('app.views.upload_image_bytes')
def test_full_flow(mock_upload, mock_email):
    # Setup mock Cloudinary returns
    mock_upload.side_effect = [
        {'secure_url': 'http://cloudinary/orig.png'},
        {'secure_url': 'http://cloudinary/stego.png'}
    ]
    
    # We also need to mock urllib.request.urlopen for the decode flow
    client = Client()
    email = "test@example.com"
    password = "MySuperSecretPassword"
    message = "Hidden Payload 123"
    
    print("\n--- 1. Testing OTP Generation (Encode) ---")
    resp_otp = client.post('/send-otp', json.dumps({'email': email}), content_type='application/json')
    assert resp_otp.json()['success'] == True
    otp = cache.get(f"otp_{email}")
    print(f"OTP Generated: {otp}")
    
    print("\n--- 2. Testing Encode POST ---")
    # Create a dummy image
    from PIL import Image
    img = Image.new('RGB', (50, 50), color='blue')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_file = SimpleUploadedFile("test.png", img_io.getvalue(), content_type="image/png")
    
    resp_encode = client.post('/encode', {
        'email': email,
        'title': 'Secret File',
        'message': message,
        'password': password,
        'otp': otp,
        'originalImage': img_file
    })
    # redirect to home
    assert resp_encode.status_code == 302
    
    record = Encode.objects.get(email=email)
    print(f"Record saved successfully: ID={record.id}, original_url={record.original_image_url}, stego_url={record.stego_image_url}")
    
    print("\n--- 3. Testing Verify Decode ---")
    resp_verify = client.post('/verify-decode', json.dumps({
        'Decode': {'email': email, 'password': password}
    }), content_type='application/json')
    verify_data = resp_verify.json()
    assert verify_data['success'] == True
    assert len(verify_data['encryptions']) == 1
    enc_id = verify_data['encryptions'][0]['_id']
    decode_otp = cache.get(f"decode_otp_{email}")
    print(f"Decode verified. OTP Generated: {decode_otp}")
    
    print("\n--- 4. Testing Reveal Message ---")
    # We must mock urllib.request.urlopen to return the stego bytes that were generated
    # Since we mocked upload, we don't have the real stego bytes URL in the cloud.
    # We will grab the stego_bytes from the mock call args to supply them back.
    stego_bytes_sent_to_cloud = mock_upload.call_args_list[1][0][0]
    
    with patch('app.views.urllib.request.urlopen') as mock_urlopen:
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = stego_bytes_sent_to_cloud
        
        resp_reveal = client.post('/reveal-message', json.dumps({
            'Decode': {
                'email': email,
                'password': password,
                'otp': decode_otp,
                'encryptionId': enc_id
            }
        }), content_type='application/json')
        
        reveal_data = resp_reveal.json()
        assert reveal_data['success'] == True
        print(f"Decoded Message: {reveal_data['message']}")
        assert reveal_data['message'] == message
        
    print("\n--- ALL TESTS PASSED ---")

if __name__ == '__main__':
    test_full_flow()
