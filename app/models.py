from django.db import models

class Encode(models.Model):
    title = models.CharField(max_length=100)
    original_image_url = models.URLField(max_length=500)
    original_image_filename = models.CharField(max_length=255)
    stego_image_url = models.URLField(max_length=500)
    stego_image_filename = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)  # Will store the Django PBKDF2 hash
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['email', 'title'], name='unique_email_title')
        ]

    def __str__(self):
        return f"{self.title} ({self.email})"
