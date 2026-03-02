from rest_framework import serializers
from .models import UploadImageModel
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UploadImageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UploadImageModel
        fields = ['id', 'user', 'image', 'uploaded_at', 'description', 'diving_site']
        read_only_fields = ['id', 'user', 'uploaded_at']
