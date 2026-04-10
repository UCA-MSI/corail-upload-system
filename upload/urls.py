from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.index, name='index'),
    path('login/', web_views.login_view, name='login'),
    path('register/', web_views.register_view, name='register'),
    path('activate/<int:user_id>/<uuid:token>/', web_views.activate_view, name='activate'),
    path('logout/', web_views.logout_view, name='logout'),
    path('upload/', web_views.upload_view, name='upload'),
    path('upload/delete/<int:image_id>/', web_views.delete_image_view, name='delete_image'),
]
