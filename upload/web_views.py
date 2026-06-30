from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db import models
import secrets
import string
from .models import UploadImageModel, UserRegistration, UserDiveSite


def index(request):
    return render(request, 'upload/index.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/upload/')
    
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                error = 'Account not activated. Please check your email for the activation link.'
            else:
                login(request, user)
                return redirect('/upload/')
        else:
            error = 'Invalid username or password'
    
    return render(request, 'upload/login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/upload/')
    
    error = None
    success = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        if User.objects.filter(username=username).exists():
            error = 'Username already exists'
        elif User.objects.filter(email=email).exists():
            error = 'Email already registered'
        else:
            # Generate temporary password
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            
            # Create user (inactive)
            user = User.objects.create_user(username=username, email=email, password=temp_password, is_active=False)
            
            # Create registration record
            UserRegistration.objects.create(
                user=user,
                email=email,
                temp_password=temp_password
            )
            
            activation_link = request.build_absolute_uri(f'/activate/{user.id}/{user.userregistration.token}/')

            send_mail(
                subject='Activate your Corail account',
                message=f'Click the link below to activate your account:\n\n{activation_link}',
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[email],
                fail_silently=False,
            )

            return render(request, 'upload/register_success.html', {'email': email})
    
    return render(request, 'upload/register.html', {'error': error})


def activate_view(request, user_id, token):
    error = None
    success = None
    
    try:
        registration = UserRegistration.objects.get(user_id=user_id, token=token)
        
        if not registration.user.is_active:
            if request.method == 'POST':
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                
                if password != confirm_password:
                    error = 'Passwords do not match'
                elif len(password) < 6:
                    error = 'Password must be at least 6 characters'
                else:
                    registration.user.set_password(password)
                    registration.user.is_active = True
                    registration.user.save()
                    registration.delete()
                    
                    success = 'Account activated! You can now login.'
                    return render(request, 'upload/activate_success.html', {'success': success})
            return render(request, 'upload/activate.html', {})
        else:
            error = 'Account already activated'
    except UserRegistration.DoesNotExist:
        error = 'Invalid activation link'
    
    return render(request, 'upload/activate.html', {'error': error})


@login_required(login_url='/login/')
def delete_image_view(request, image_id):
    if request.method == 'POST':
        try:
            image = UploadImageModel.objects.get(id=image_id, user=request.user)
            image.image.delete(save=False)
            image.delete()
        except UploadImageModel.DoesNotExist:
            pass
    return redirect('/upload/')


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required(login_url='/login/')
def profile_view(request):
    """Display and update the authenticated user's profile dive-site log."""
    error = None
    known_sites = (
        UploadImageModel.objects
        .exclude(diving_site='')
        .values_list('diving_site', flat=True)
        .distinct()
        .order_by('diving_site')
    )

    if request.method == 'POST':
        dive_site = request.POST.get('dive_site', '').strip()
        latitude = request.POST.get('latitude', '').strip() or None
        longitude = request.POST.get('longitude', '').strip() or None
        depth = request.POST.get('depth', '').strip() or None

        if not dive_site:
            error = 'Please select a dive site.'
        else:
            UserDiveSite.objects.create(
                user=request.user,
                dive_site=dive_site,
                latitude=latitude,
                longitude=longitude,
                depth=depth,
            )
            messages.success(request, 'Dive site added to your profile.')
            return redirect('/profile/')

    entries = UserDiveSite.objects.filter(user=request.user).order_by('-added_at')
    return render(request, 'upload/profile.html', {
        'error': error,
        'known_sites': known_sites,
        'entries': entries,
    })


@login_required(login_url='/login/')
def delete_dive_site_view(request, entry_id):
    """Remove a dive-site entry from the authenticated user's profile."""
    if request.method == 'POST':
        UserDiveSite.objects.filter(id=entry_id, user=request.user).delete()
    return redirect('/profile/')


@login_required(login_url='/login/')
def upload_view(request):
    error = None
    success = None
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        description = request.POST.get('description', '')
        diving_site = request.POST.get('diving_site', '')
        diving_date = request.POST.get('diving_date', '')
        
        if images:
            for image in images:
                UploadImageModel.objects.create(
                    user=request.user,
                    image=image,
                    description=description,
                    diving_site=diving_site,
                    diving_date=diving_date or None
                )
            count = len(images)
            messages.success(request, f'{count} image{"s" if count > 1 else ""} uploaded successfully!')
            return redirect('/upload/')
        else:
            error = 'Please select at least one image'

    images = UploadImageModel.objects.filter(user=request.user).order_by(
        models.F('diving_date').desc(nulls_last=True), '-uploaded_at'
    )
    return render(request, 'upload/upload.html', {
        'error': error,
        'success': success,
        'images': images
    })
