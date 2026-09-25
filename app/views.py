import json
import urllib.request
import os
import bcrypt
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.cache import cache
from django.db import IntegrityError

from .models import Encode
from .services.steganography import encode_image, decode_image
from .services.encryption import encrypt_message, decrypt_message
from .services.email_service import generate_otp, send_otp_email
from .services.cloudinary_service import upload_image_bytes

# Simple Views
def home(request):
    return render(request, 'pages/home.html')

def about(request):
    return render(request, 'pages/about.html')

# Encoding
def encode_page(request):
    if request.method == "POST":
        try:
            # 1. Extract data
            email = request.POST.get('Encode[email]')
            title = request.POST.get('Encode[title]')
            message = request.POST.get('Encode[message]')
            password = request.POST.get('Encode[password]')
            otp = request.POST.get('Encode[otp]')
            original_image = request.FILES.get('originalImage')
            
            if not original_image:
                messages.error(request, "Image is required.")
                return redirect('encode_page')
            
            # 2. Validate OTP
            cached_otp = cache.get(f"otp_{email}")
            if not cached_otp or cached_otp != otp:
                messages.error(request, "Invalid or expired OTP.")
                return redirect('encode_page')
                
            # Clear OTP after successful use
            cache.delete(f"otp_{email}")
            
            # Hash password with bcrypt cost 12
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
            
            # 3. Encrypt the secret message
            encrypted_payload = encrypt_message(message, password)
            
            # 4. Read image bytes and perform steganography
            image_bytes = original_image.read()
            stego_bytes = encode_image(image_bytes, encrypted_payload)
            
            # 5. Upload original image to Cloudinary (stegohide_DEV/originals)
            orig_result = upload_image_bytes(image_bytes, f"orig_{original_image.name}", folder="stegohide_DEV/originals")
            
            # 6. Upload stego image to Cloudinary (stegohide_DEV/stegos)
            stego_result = upload_image_bytes(stego_bytes, f"stego_{original_image.name}", folder="stegohide_DEV/stegos")
            
            # 7. Save to Database
            Encode.objects.create(
                email=email,
                title=title,
                password=hashed_password,
                original_image_url=orig_result['secure_url'],
                original_image_filename=original_image.name,
                stego_image_url=stego_result['secure_url'],
                stego_image_filename=f"encoded_{original_image.name}"
            )
            
            messages.success(request, "Message encoded successfully!")
            return redirect('home')
            
        except IntegrityError:
            messages.error(request, f"You already have a record with the title '{title}'. Please choose a different title.")
            return redirect('encode_page')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('encode_page')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return redirect('encode_page')
            
    return render(request, 'pages/encode.html')

def send_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            
            otp = generate_otp()
            # Store in cache for 5 minutes (300 seconds)
            cache.set(f"otp_{email}", otp, timeout=300)
            
            success = send_otp_email(email, otp)
            if success:
                return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send OTP email'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

# Decoding
def decode_page(request):
    return render(request, 'pages/decode.html')

def verify_decode(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            decode_data = data.get('Decode', {})
            email = decode_data.get('email')
            password = decode_data.get('password')
            
            if not email or not password:
                return JsonResponse({'success': False, 'error': 'Email and password are required'}, status=400)
                
            records = Encode.objects.filter(email=email)
            matching_records = []
            
            # bcrypt check
            for record in records:
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), record.password.encode('utf-8')):
                        matching_records.append(record)
                except Exception:
                    pass # ignore malformed hashes
                    
            if not matching_records:
                return JsonResponse({'success': False, 'error': 'No matching records found for the given email and password.'}, status=404)
                
            # Generate OTP and store it against the user's email
            otp = generate_otp()
            cache.set(f"decode_otp_{email}", otp, timeout=300)
            
            success = send_otp_email(email, otp)
            if not success:
                return JsonResponse({'success': False, 'error': 'Failed to send OTP email'}, status=500)
                
            encryptions = []
            for r in matching_records:
                encryptions.append({
                    '_id': str(r.id),
                    'title': r.title,
                    'createdAt': r.created_at.isoformat()
                })
                
            return JsonResponse({
                'success': True,
                'message': 'OTP sent successfully. Please check your email.',
                'encryptions': encryptions
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def reveal_message(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            decode_data = data.get('Decode', {})
            email = decode_data.get('email')
            password = decode_data.get('password')
            otp = decode_data.get('otp')
            encryption_id = decode_data.get('encryptionId')
            
            if not all([email, password, otp, encryption_id]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
                
            # Verify OTP
            cached_otp = cache.get(f"decode_otp_{email}")
            if not cached_otp or cached_otp != otp:
                return JsonResponse({'success': False, 'error': 'Invalid or expired OTP'}, status=400)
                
            # Retrieve record
            try:
                record = Encode.objects.get(id=encryption_id, email=email)
            except Encode.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
                
            # Verify password
            try:
                if not bcrypt.checkpw(password.encode('utf-8'), record.password.encode('utf-8')):
                    return JsonResponse({'success': False, 'error': 'Incorrect password'}, status=401)
            except Exception:
                return JsonResponse({'success': False, 'error': 'Incorrect password'}, status=401)
                
            # Fetch the image bytes from Cloudinary
            req = urllib.request.Request(record.stego_image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                image_bytes = response.read()
                
            # Decode the LSB steganography
            encrypted_payload = decode_image(image_bytes)
            
            # Decrypt the AES message
            try:
                decrypted_message = decrypt_message(encrypted_payload, password)
                # Clear OTP
                cache.delete(f"decode_otp_{email}")
                return JsonResponse({'success': True, 'message': decrypted_message})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Incorrect password or corrupted data'}, status=401)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Extraction failed: {str(e)}"}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

# Admin
def admin_page(request):
    is_admin = request.session.get('is_admin', False)
    total_records = Encode.objects.count() if is_admin else 0
    return render(request, 'pages/admin.html', {'total_records': total_records})

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        env_user = os.environ.get('ADMIN_USERNAME')
        env_pass = os.environ.get('ADMIN_PASSWORD')
        
        if username == env_user and password == env_pass:
            request.session['is_admin'] = True
            messages.success(request, "Logged in successfully.")
        else:
            messages.error(request, "Invalid admin credentials.")
            
    return redirect('admin_page')

def admin_logout(request):
    if request.method == "POST":
        request.session['is_admin'] = False
        messages.success(request, "Logged out successfully.")
    return redirect('admin_page')

def admin_listings(request):
    if not request.session.get('is_admin', False):
        messages.error(request, "Unauthorized access.")
        return redirect('admin_page')
        
    all_data = Encode.objects.all().order_by('-created_at')
    return render(request, 'pages/listing.html', {'allData': all_data})

def admin_extract_message(request):
    if not request.session.get('is_admin', False):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
        
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Admin payload: { stegoImageUrl: stegoUrl, recordId: recordId, password: password }
            stego_image_url = data.get('stegoImageUrl')
            record_id = data.get('recordId')
            password = data.get('password')
            
            if not stego_image_url or not password or not record_id:
                return JsonResponse({'success': False, 'error': 'Image URL, record ID, and password are required'})
                
            try:
                record = Encode.objects.get(id=record_id)
            except Encode.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
                
            # Fetch the image bytes from Cloudinary
            req = urllib.request.Request(stego_image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                image_bytes = response.read()
                
            # Decode the LSB steganography
            encrypted_payload = decode_image(image_bytes)
            
            # Decrypt the AES message
            try:
                decrypted_message = decrypt_message(encrypted_payload, password)
                return JsonResponse({'success': True, 'message': decrypted_message})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Incorrect password or corrupted data'}, status=401)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Extraction failed: {str(e)}"}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
