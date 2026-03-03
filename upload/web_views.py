from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import secrets
import string
from .models import UploadImageModel, UserRegistration


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
            
            # In production, send email here
            # For now, show the link in the response

            activation_link = request.build_absolute_uri(f'/activate/{user.id}/{user.userregistration.token}/')
            
            success = f'Registration request submitted! An email has been sent to {email}.'
            
            # Store link for demo purposes (remove in production)
            request.session['demo_activation_link'] = activation_link
            
            return render(request, 'upload/register_success.html', {
                'success': success,
                'email': email,
                'activation_link': activation_link
            })
    
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


def logout_view(request):
    logout(request)
    return redirect('/')


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
            success = f'{count} image{"s" if count > 1 else ""} uploaded successfully!'
        else:
            error = 'Please select at least one image'
    
    images = UploadImageModel.objects.filter(user=request.user).order_by('-diving_date', '-uploaded_at')
    return render(request, 'upload/upload.html', {
        'error': error,
        'success': success,
        'images': images
    })
