from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='root'),
    path('home', views.home, name='home'),
    path('about', views.about, name='about'),
    
    # Encryption (Steganography + AES)
    path('encode', views.encode_page, name='encode_page'),
    path('send-otp', views.send_otp, name='send_otp'),
    
    # Decryption
    path('decode', views.decode_page, name='decode_page'),
    path('verify-decode', views.verify_decode, name='verify_decode'),
    path('reveal-message', views.reveal_message, name='reveal_message'),
    
    # Admin Interface
    path('admin', views.admin_page, name='admin_page'),
    path('admin/login', views.admin_login, name='admin_login'),
    path('admin/logout', views.admin_logout, name='admin_logout'),
    path('listings', views.admin_listings, name='admin_listings'),
    path('extract-message', views.admin_extract_message, name='admin_extract_message'),
]
