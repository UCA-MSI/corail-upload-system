from django.contrib import admin
from .models import UploadImageModel, UserRegistration, UserProfile, DiveSite, UserDiveSite

admin.site.register(UploadImageModel)
admin.site.register(UserRegistration)
admin.site.register(UserProfile)
admin.site.register(UserDiveSite)


@admin.register(DiveSite)
class DiveSiteAdmin(admin.ModelAdmin):
    list_display = (
        'site_id', 'name', 'depth', 'country', 'region', 'latitude', 'longitude',
    )
    list_filter = ('country', 'source_version')
    search_fields = ('site_id', 'name', 'region')

    def has_change_permission(self, request, obj=None) -> bool:
        """Reference sites imported from coraldb are read-only."""
        if obj is not None and obj.is_reference:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        """Reference sites imported from coraldb cannot be deleted."""
        if obj is not None and obj.is_reference:
            return False
        return super().has_delete_permission(request, obj)
