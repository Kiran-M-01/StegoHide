import cloudinary
import cloudinary.uploader
from django.conf import settings

# Ensure Cloudinary is configured using settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

def upload_image_bytes(image_bytes: bytes, filename: str, folder: str = "StegoHide") -> dict:
    """
    Uploads raw image bytes to Cloudinary.
    Args:
        image_bytes: The image file bytes.
        filename: Optional filename for the public_id.
        folder: The destination folder on Cloudinary.
    Returns:
        A dictionary containing the upload result, notably 'secure_url'.
    """
    # Cloudinary python SDK can accept bytes directly
    result = cloudinary.uploader.upload(
        image_bytes,
        folder=folder,
        resource_type="image",
        # Use filename as part of public_id if desired, but Cloudinary auto-generates fine too
    )
    return result

def delete_image(public_id: str):
    """
    Deletes an image from Cloudinary given its public_id.
    """
    cloudinary.uploader.destroy(public_id)
