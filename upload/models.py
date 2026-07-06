from django.db import models
from django.contrib.auth.models import User
import uuid

ORGANISATION_TYPE_CHOICES = [
    ('academia', 'Academia'),
    ('ngo', 'NGO / Non-profit'),
    ('private', 'Private'),
]

DEPTH_CHOICES = [
    ('0_5m', '0 – 5 m'),
    ('5_10m', '5 – 10 m'),
    ('gt_10m', '> 10 m'),
    ('custom', 'Free entry'),
]

WATER_CONDITION_CHOICES = [
    ('clear', 'Clear'),
    ('murky', 'Murky'),
    ('turbid', 'Turbid'),
    ('low_vis', 'Low visibility'),
    ('good_vis', 'Good visibility'),
]

WEATHER_CONDITION_CHOICES = [
    ('sunny', 'Sunny'),
    ('partly_cloudy', 'Partly cloudy'),
    ('cloudy', 'Cloudy'),
    ('overcast', 'Overcast'),
    ('rainy', 'Rainy'),
    ('stormy', 'Stormy'),
]


class DiveSite(models.Model):
    """Canonical dive site registry shared across all users."""

    name = models.CharField(max_length=255, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_sites'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class UploadImageModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    diving_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    dive_site = models.ForeignKey(
        DiveSite, on_delete=models.SET_NULL, null=True, blank=True, related_name='images'
    )
    photographer_name = models.CharField(max_length=255, blank=True)
    photographer_surname = models.CharField(max_length=255, blank=True)
    photographer_email = models.EmailField(blank=True)
    dive_master_name = models.CharField(max_length=255, blank=True)
    dive_master_surname = models.CharField(max_length=255, blank=True)
    dive_master_email = models.EmailField(blank=True)
    depth_category = models.CharField(max_length=10, choices=DEPTH_CHOICES, blank=True)
    depth_custom = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    water_temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    water_conditions = models.CharField(max_length=15, choices=WATER_CONDITION_CHOICES, blank=True)
    weather_conditions = models.CharField(max_length=15, choices=WEATHER_CONDITION_CHOICES, blank=True)

    def __str__(self) -> str:
        return f"Image {self.id} uploaded at {self.uploaded_at}"


class UserProfile(models.Model):
    """Extended profile for an authenticated user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organisation_type = models.CharField(
        max_length=20, choices=ORGANISATION_TYPE_CHOICES, blank=True
    )
    organisation_responsible = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"Profile of {self.user.username}"


class UserRegistration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    temp_password = models.CharField(max_length=128)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Registration for {self.user.username}"


class UserDiveSite(models.Model):
    """A user's personal dive log entry linking them to a dive site."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dive_sites')
    dive_site = models.ForeignKey(
        DiveSite, on_delete=models.CASCADE, null=True, blank=True, related_name='user_logs'
    )
    depth = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} — {self.dive_site}"
