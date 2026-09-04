from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
import secrets
import string
import uuid
from .models import (
    UploadImageModel, UserRegistration, UserProfile,
    DiveSite, UserDiveSite,
    ORGANISATION_TYPE_CHOICES, DIVE_TIME_CHOICES, DEPTH_CHOICES,
    WATER_CONDITION_CHOICES, WEATHER_CONDITION_CHOICES,
)


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

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            error = 'Username already exists'
        elif User.objects.filter(email=email).exists():
            error = 'Email already registered'
        else:
            temp_password = ''.join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
            )
            user = User.objects.create_user(
                username=username, email=email, password=temp_password, is_active=False
            )
            UserRegistration.objects.create(
                user=user, email=email, temp_password=temp_password
            )
            activation_link = request.build_absolute_uri(
                f'/activate/{user.id}/{user.userregistration.token}/'
            )
            send_mail(
                subject='Activate your Corail account',
                message=f'Click the link below to activate your account:\n\n{activation_link}',
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
            return render(request, 'upload/register_success.html', {'email': email})

    return render(request, 'upload/register.html', {'error': error})


def activate_view(request, user_id, token):
    error = None

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
                    return render(request, 'upload/activate_success.html', {
                        'success': 'Account activated! You can now login.'
                    })
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
def profile_view(request):
    """Display and update the authenticated user's profile and dive-site log."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.save(update_fields=['first_name', 'last_name'])

            profile.organisation_type = request.POST.get('organisation_type', '')
            profile.organisation_responsible = request.POST.get('organisation_responsible', '').strip()
            profile.country = request.POST.get('country', '').strip()
            profile.location = request.POST.get('location', '').strip()
            profile.save()

            messages.success(request, 'Profile updated.')
            return redirect('/profile/')

        if action == 'add_dive_site':
            dive_site_id = request.POST.get('dive_site_id', '').strip()
            new_site_name = request.POST.get('new_site_name', '').strip()
            depth = request.POST.get('depth', '').strip() or None

            dive_site = None
            if dive_site_id:
                dive_site = DiveSite.objects.filter(id=dive_site_id).first()
            elif new_site_name:
                country = request.POST.get('new_site_country', '').strip() or 'Indonesia'
                region = request.POST.get('new_site_region', '').strip()
                lat = request.POST.get('new_site_lat', '').strip() or None
                lon = request.POST.get('new_site_lon', '').strip() or None
                dive_site, _ = DiveSite.objects.get_or_create(
                    name=new_site_name,
                    defaults={
                        'country': country, 'region': region,
                        'latitude': lat, 'longitude': lon, 'created_by': request.user,
                    },
                )

            if dive_site:
                UserDiveSite.objects.create(user=request.user, dive_site=dive_site, depth=depth)
                messages.success(request, 'Dive site added to your log.')
            else:
                messages.error(request, 'Please select or enter a dive site.')
            return redirect('/profile/')

    dive_sites = DiveSite.objects.all().order_by('region', 'name')
    entries = (
        UserDiveSite.objects
        .filter(user=request.user)
        .select_related('dive_site')
        .order_by('-added_at')
    )
    return render(request, 'upload/profile.html', {
        'profile': profile,
        'dive_sites': dive_sites,
        'entries': entries,
        'organisation_type_choices': ORGANISATION_TYPE_CHOICES,
    })


@login_required(login_url='/login/')
def delete_dive_site_view(request, entry_id):
    """Remove a dive-site log entry scoped to the authenticated user."""
    if request.method == 'POST':
        UserDiveSite.objects.filter(id=entry_id, user=request.user).delete()
    return redirect('/profile/')


@login_required(login_url='/login/')
def upload_view(request):
    """Handle image uploads with full dive metadata."""
    error = None

    if request.method == 'POST':
        images = request.FILES.getlist('images')

        # Dive site: must be selected from the existing registry (created via the profile page)
        dive_site_id = request.POST.get('dive_site_id', '').strip()
        dive_site = DiveSite.objects.filter(id=dive_site_id).first() if dive_site_id else None

        diving_date = request.POST.get('diving_date', '').strip() or None
        depth_custom = request.POST.get('depth_custom', '').strip() or None
        water_temperature = request.POST.get('water_temperature', '').strip() or None

        common_fields = dict(
            description=request.POST.get('description', ''),
            dive_site=dive_site,
            diving_date=diving_date,
            dive_time=request.POST.get('dive_time', ''),
            photographer_name=request.POST.get('photographer_name', ''),
            photographer_surname=request.POST.get('photographer_surname', ''),
            photographer_email=request.POST.get('photographer_email', ''),
            dive_master_name=request.POST.get('dive_master_name', ''),
            dive_master_surname=request.POST.get('dive_master_surname', ''),
            dive_master_email=request.POST.get('dive_master_email', ''),
            depth_category=request.POST.get('depth_category', ''),
            depth_custom=depth_custom,
            water_temperature=water_temperature,
            water_conditions=request.POST.get('water_conditions', ''),
            weather_conditions=request.POST.get('weather_conditions', ''),
        )

        if not diving_date:
            error = 'Please enter the diving date'
        elif images:
            session_id = uuid.uuid4()
            for image in images:
                UploadImageModel.objects.create(
                    user=request.user, image=image, session_id=session_id, **common_fields
                )
            count = len(images)
            messages.success(request, f'{count} image{"s" if count > 1 else ""} uploaded successfully!')
            return redirect('/upload/')
        else:
            error = 'Please select at least one image'

    sessions = _get_upload_sessions(request.user)
    dive_sites = DiveSite.objects.all().order_by('region', 'name')
    photographer_prefill = {
        'name': request.user.first_name,
        'surname': request.user.last_name,
        'email': request.user.email,
    }
    return render(request, 'upload/upload.html', {
        'error': error,
        'sessions': sessions,
        'filter_options': _get_session_filter_options(sessions),
        'dive_sites': dive_sites,
        'photographer_prefill': photographer_prefill,
        'dive_time_choices': DIVE_TIME_CHOICES,
        'depth_choices': DEPTH_CHOICES,
        'water_condition_choices': WATER_CONDITION_CHOICES,
        'weather_condition_choices': WEATHER_CONDITION_CHOICES,
    })


def _depth_label(image):
    """Human-readable depth for one image, e.g. '5 m' or '22.5 m'."""
    if image.depth_category == 'custom' and image.depth_custom:
        return f'{image.depth_custom} m'
    if image.depth_category:
        return image.get_depth_category_display()
    return ''


def _water_temp_label(image):
    """Human-readable water temperature for one image, e.g. '26.5 °C'."""
    return f'{image.water_temperature} °C' if image.water_temperature is not None else ''


def _get_upload_sessions(user):
    """Group a user's uploaded images by session, one representative image each."""
    images = UploadImageModel.objects.filter(user=user).select_related('dive_site').order_by(
        models.F('diving_date').desc(nulls_last=True), '-uploaded_at'
    )
    sessions = {}
    for image in images:
        session = sessions.setdefault(image.session_id, image)
        session.image_count = getattr(session, 'image_count', 0) + 1
    for session in sessions.values():
        session.depth_label = _depth_label(session)
        session.water_temp_label = _water_temp_label(session)
    return list(sessions.values())


def _get_session_filter_options(sessions):
    """Distinct, sorted values actually present in `sessions`, for the table's dropdown filters."""
    return {
        'date': sorted({str(s.diving_date) for s in sessions if s.diving_date}),
        'site': sorted({s.dive_site.name for s in sessions if s.dive_site}),
        'time': sorted({s.get_dive_time_display() for s in sessions if s.dive_time}),
        'weather': sorted({s.get_weather_conditions_display() for s in sessions if s.weather_conditions}),
        'depth': sorted({s.depth_label for s in sessions if s.depth_label}),
        'water_temp': sorted({s.water_temp_label for s in sessions if s.water_temp_label}),
        'water_conditions': sorted({s.get_water_conditions_display() for s in sessions if s.water_conditions}),
    }


@login_required(login_url='/login/')
def session_detail_view(request, session_id):
    """List the images of one upload session and let the user edit each one."""
    if request.method == 'POST':
        action = request.POST.get('action', 'edit_image')

        if action == 'edit_session':
            _update_session_date_and_site(request, session_id)
            return redirect('session_detail', session_id=session_id)

        image_id = request.POST.get('image_id', '').strip()
        image = UploadImageModel.objects.filter(
            id=image_id, user=request.user, session_id=session_id
        ).first()

        if image:
            dive_site_id = request.POST.get('dive_site_id', '').strip()
            image.dive_site = DiveSite.objects.filter(id=dive_site_id).first() if dive_site_id else None
            image.diving_date = request.POST.get('diving_date', '').strip() or image.diving_date
            image.dive_time = request.POST.get('dive_time', '')
            image.description = request.POST.get('description', '')
            image.photographer_name = request.POST.get('photographer_name', '')
            image.photographer_surname = request.POST.get('photographer_surname', '')
            image.photographer_email = request.POST.get('photographer_email', '')
            image.dive_master_name = request.POST.get('dive_master_name', '')
            image.dive_master_surname = request.POST.get('dive_master_surname', '')
            image.dive_master_email = request.POST.get('dive_master_email', '')
            image.depth_category = request.POST.get('depth_category', '')
            image.depth_custom = request.POST.get('depth_custom', '').strip() or None
            image.water_temperature = request.POST.get('water_temperature', '').strip() or None
            image.water_conditions = request.POST.get('water_conditions', '')
            image.weather_conditions = request.POST.get('weather_conditions', '')
            image.save()
            messages.success(request, 'Picture updated.')
        return redirect('session_detail', session_id=session_id)

    images = list(
        UploadImageModel.objects.filter(user=request.user, session_id=session_id)
        .select_related('dive_site').order_by('id')
    )

    if not images:
        messages.error(request, 'Upload session not found.')
        return redirect('/upload/')

    dive_sites = DiveSite.objects.all().order_by('region', 'name')
    return render(request, 'upload/session_detail.html', {
        'session_id': session_id,
        'images': images,
        'representative': images[0],
        'dive_sites': dive_sites,
        'dive_time_choices': DIVE_TIME_CHOICES,
        'depth_choices': DEPTH_CHOICES,
        'water_condition_choices': WATER_CONDITION_CHOICES,
        'weather_condition_choices': WEATHER_CONDITION_CHOICES,
    })


def _update_session_date_and_site(request, session_id):
    """Apply a shared diving date and dive site to every picture in a session at once."""
    diving_date = request.POST.get('diving_date', '').strip()
    if not diving_date:
        messages.error(request, 'Please enter the diving date.')
        return

    dive_site_id = request.POST.get('dive_site_id', '').strip()
    dive_site = DiveSite.objects.filter(id=dive_site_id).first() if dive_site_id else None

    UploadImageModel.objects.filter(user=request.user, session_id=session_id).update(
        diving_date=diving_date, dive_site=dive_site
    )
    messages.success(request, 'Date and site updated for all pictures in this session.')


@login_required(login_url='/login/')
def delete_image_view(request, image_id):
    if request.method == 'POST':
        try:
            image = UploadImageModel.objects.get(id=image_id, user=request.user)
            image.image.delete(save=False)
            image.delete()
        except UploadImageModel.DoesNotExist:
            pass
    return redirect(request.POST.get('next') or '/upload/')
