from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UploadImageModel


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
            login(request, user)
            return redirect('/upload/')
        else:
            error = 'Invalid username or password'
    
    return render(request, 'upload/login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/upload/')
    
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            error = 'Passwords do not match'
        elif User.objects.filter(username=username).exists():
            error = 'Username already exists'
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('/upload/')
    
    return render(request, 'upload/register.html', {'error': error})


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
