from django.db import models
from django.contrib.auth.models import User
import uuid


class UploadImageModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    diving_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    diving_site = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image {self.id} uploaded at {self.uploaded_at}"


class UserRegistration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    temp_password = models.CharField(max_length=128)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Registration for {self.user.username}"


class UserDiveSite(models.Model):
    """A dive site entry logged by a user, with GPS coordinates and depth."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dive_sites')
    dive_site = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    depth = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.dive_site}"
