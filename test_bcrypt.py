import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import bcrypt
from app.models import Encode

def test_password():
    password = "MySecurePassword"
    
    # Simulate Encode
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    e = Encode(title="Test", email="test@test.com", password=hashed)
    
    # Verify success
    assert bcrypt.checkpw(password.encode('utf-8'), e.password.encode('utf-8')) == True
    print("SUCCESS: Password verified")
    
    # Verify failure
    assert bcrypt.checkpw("WrongPassword".encode('utf-8'), e.password.encode('utf-8')) == False
    print("SUCCESS: Wrong password rejected")

if __name__ == '__main__':
    test_password()
