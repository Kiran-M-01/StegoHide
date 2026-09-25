import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp() -> str:
    """Generates a 6-digit numerical OTP."""
    return str(random.randint(100000, 999999))

def send_otp_email(recipient_email: str, otp: str) -> bool:
    """
    Sends the OTP to the recipient's email using Django's email backend.
    Returns True if successful, False otherwise.
    """
    subject = "Your StegoHide OTP"
    message = (
        f"Your One Time Password (OTP) for StegoHide is: {otp}\n\n"
        f"This OTP is valid for 5 minutes. Do not share it with anyone."
    )
    
    try:
        # send_mail returns the number of successfully delivered messages
        num_sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return num_sent > 0
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False
