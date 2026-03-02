from django.db import models
from django.contrib.auth.models import User


class UploadImageModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    diving_site = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image {self.id} uploaded at {self.uploaded_at}"
