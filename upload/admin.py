from django.contrib import admin
from .models import UploadImageModel, UserRegistration, UserProfile, DiveSite, UserDiveSite

admin.site.register(UploadImageModel)
admin.site.register(UserRegistration)
admin.site.register(UserProfile)
admin.site.register(UserDiveSite)


@admin.register(DiveSite)
class DiveSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'region', 'latitude', 'longitude')
    list_filter = ('country',)
    search_fields = ('name', 'region')
