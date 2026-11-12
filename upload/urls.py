from django.urls import path
from . import api_views, web_views

BACKUP_API = 'api/backup/'

urlpatterns = [
    path(f'{BACKUP_API}db/', api_views.db_snapshot_view, name='backup_db'),
    path(f'{BACKUP_API}status/', api_views.backlog_status_view, name='backup_status'),
    path(
        f'{BACKUP_API}originals/',
        api_views.originals_manifest_view,
        name='backup_originals',
    ),
    path(
        f'{BACKUP_API}originals/<int:upload_id>/',
        api_views.original_download_view,
        name='backup_original',
    ),
    path(
        f'{BACKUP_API}originals/<int:upload_id>/ack/',
        api_views.original_ack_view,
        name='backup_original_ack',
    ),
    path('', web_views.index, name='index'),
    path('login/', web_views.login_view, name='login'),
    path('register/', web_views.register_view, name='register'),
    path('activate/<int:user_id>/<uuid:token>/', web_views.activate_view, name='activate'),
    path('logout/', web_views.logout_view, name='logout'),
    path('upload/', web_views.upload_view, name='upload'),
    path('upload/session/<uuid:session_id>/', web_views.session_detail_view, name='session_detail'),
    path(
        'upload/thumbnail/<int:image_id>/',
        web_views.thumbnail_view,
        name='thumbnail',
    ),
    path('upload/delete/<int:image_id>/', web_views.delete_image_view, name='delete_image'),
    path('profile/', web_views.profile_view, name='profile'),
    path('profile/delete/<int:entry_id>/', web_views.delete_dive_site_view, name='delete_dive_site'),
]
