from django.contrib import admin
from .models import UploadImageModel, UserRegistration, UserProfile, DiveSite, UserDiveSite

admin.site.register(UploadImageModel)
admin.site.register(UserRegistration)
admin.site.register(UserProfile)
admin.site.register(DiveSite)
admin.site.register(UserDiveSite)
