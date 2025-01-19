import base64
from datetime import timedelta, datetime
import os
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import qrcode
from .forms import UserProfileForm,PaymentProofForm,EventForm, PlaceForm,CongressDateForm,TopicAreaForm,SubmissionForm,SubmissionFileForm,AuthorForm
from .models import UserProfile,PaymentProof,Place,CongressDate,Event,Registration,adminPermissions,TopicArea,Submission,reviewersCodes
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django_countries import countries
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from .models import CustomUser,SubmissionFile

import pycountry
from io import BytesIO
from collections import defaultdict

##FOR VALIDATING EMAILS
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# PARA DIPLOMAS
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter, PdfReader
import os
import smtplib
import requests
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
# PARA DIPLOMAS

#PARA SUBIR ARCHIVOS A LO BANNERS
from django.core.files.storage import FileSystemStorage

#PARA REVISAR SI ES SUPER USUARIO
from .decorators import superuser_required,completedProfileRequired

from django.http import HttpResponseNotFound,HttpResponseRedirect

#DECORADOR PARA VERIFICAR QUE SEA AUTOR ############## FALTANTE

#PARA GENERAR SUBMISSION
from django.forms import formset_factory

#invitations to reviewers
import hashlib


#PROCESADOR DE CONTEXTO
def get_user_context_data(request):
    user_id = request.user.id
    
    try:
        user_profile = UserProfile.objects.get(user_id=user_id)
        payment_completed = user_profile.payment_completed
        allow_registration = user_profile.permitirRegistro
        user_type = user_profile.user_type
        if user_type == "author":
            is_author = True
            is_student = False
            is_public = False
        if user_type == "student":
            is_student = True
            is_author = False
            is_public = False
        if user_type == "public":
            is_public = True
            is_author = False
            is_student = False

    except ObjectDoesNotExist:
        redirect('complete_profile')
        user_profile = None
        payment_completed = False
        allow_registration = False
        user_type = "Uncompleted profile"
        is_author = False
        is_student = False
        is_public = False
        is_reviewer = False
        
    
    return {
        "userProfile": user_profile,
        "paymentCompleted": payment_completed,
        "allowRegistration": allow_registration,
        "userType": user_type,
        "is_staff_user": request.user.is_staff,
        "is_staff_superuser": request.user.is_superuser,
        "is_author": is_author,
        "is_student": is_student,
        "is_public": is_public,
        "is_reviewer": getattr(request.user, 'isReviewer', False),
    }




# Create your views here.





def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        location = request.GET.get('location', 'Peru')  # Default location
        background_image = fetch_image(location)  # Get a single image URL
        context = {
            'background_image': background_image,  # List of image URLs
            'location': location,
        }
        return render(request,'index.html',context)

def fetch_image(location):
    # Example using Pexels API
    API_KEY = 'VqPVd9RKCmdfe89nsEszb6aa8fUZRzgDiOXeAyp7PySwVI6CPXvcq4ca'  # Replace with your API key
    url = f"https://api.pexels.com/v1/search?query={location}&per_page=10"
    headers = {"Authorization": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data['photos']:
            import random
            photo = random.choice(data['photos'])
            return photo['src']['original']
    return '/static/images/bg_anual_s.jpg'  # Fallback to your static image


@login_required(login_url='google_login')
@completedProfileRequired
def dashboard(request):
    userID = request.user.id
    allowRegistration=False

    base_url = f"{request.scheme}://{request.get_host()}/"
    # Generate QR codes for each registration
    qr_text = f"{base_url}welcomeKit/{userID}/" # Update URL as needed
    qr_image = qrcode.make(qr_text)

        # Save the QR code to a BytesIO object
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_code_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Add the QR code image to the registration object for rendering
    qr_code = qr_code_image

    userProfile = UserProfile.objects.get(user_id=userID)
    paymentCompleted = userProfile.payment_completed
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    is_reviewer=request.user.isReviewer
    try:
        userType=userProfile.user_type
    except:
        userType="Uncompleted profile"
    
    banners_path = os.path.join(settings.BASE_DIR, 'mainApplication', 'static', 'images', 'banners')
    images = []

    if os.path.exists(banners_path):
        images = [f'images/banners/{img}' for img in os.listdir(banners_path) if img.endswith(('jpg', 'jpeg', 'png', 'gif'))]

    permissionValues=adminPermissions.objects.all()
    try:
        submissions = Submission.objects.filter(user_id=request.user.id,is_withdrawn=False)
        for submission in submissions:
            try:
                if submission.title and submission.keywords and submission.abstract:
                    submission.step1_status = "completed"
                else:
                    submission.step1_status = "uncompleted"
            except:                
                submission.step1_status = "uncompleted"

            if submission.step1_status == "completed":
                submission.step2_status = "completed" if submission.sent_for_review else "uncompleted"
            else:
                submission.step2_status = "pending"
            # Step 3: Check if reviewers are assigned
            if submission.step2_status == "completed":
                submission.step3_status = "completed" if submission.reviewers.exists() else "inprogress"
            else:
                submission.step3_status = "pending"
            # Step 4: Check if under reviewchito 
            if submission.step3_status == "completed":
                submission.step4_status = "completed" if submission.under_review else "inprogress"
            else:
                submission.step4_status = "pending"

            # Step 5: Check if decision issued
            if submission.step4_status == "completed":
                submission.step5_status = "completed" if submission.decision_issued() else "uncompleted"
            else:
                submission.step5_status = "pending"
    except:
        submissions = None

    context = {
        'qr':qr_code,
        'allowRegistration':allowRegistration,
        'paymentCompleted': paymentCompleted,
        'userType':userProfile,
        'is_staff_user': is_staff_user,
        'is_staff_superuser':is_staff_superuser,
        'is_reviewer':is_reviewer,
        'images': images,
        'permissionValues':permissionValues,
        'submissions':submissions,
    }
    return render(request,'dashboard.html',context)

@login_required(login_url='google_login')
def complete_profile(request):
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    try:
        # Intenta obtener el perfil existente del usuario
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Si no existe, crea uno nuevo
        profile = UserProfile(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'completeProfile.html', {'form': form,'is_staff_user':is_staff_user,'is_staff_superuser':is_staff_superuser})


@login_required(login_url='google_login')
@completedProfileRequired
def payment(request):
    userID = request.user.id
    try:
        userProfile = UserProfile.objects.get(user_id=userID)
        paymentObservations = userProfile.payment_completed
        paymentCompleted = userProfile.payment_completed
    except:
        pass
    # userProfile = UserProfile.objects.get(user_id=userID)
    uploadFiles = PaymentProof.objects.filter(user_profile=userProfile)  # Obtén todos los archivos subidos
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    isRejected = uploadFiles.first().rejected if uploadFiles.exists() else False  # Verifica si hay archivos

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            payment_proof = form.save(commit=False)
            payment_proof.user_profile = userProfile  # Associate with the logged-in user's profile
            payment_proof.save()
            return redirect('payment')  # Redirect after successful upload to avoid resubmission
    else:
        form = PaymentProofForm()

    base_url = f"{request.scheme}://{request.get_host()}/"
    # Generate QR codes for each registration
    qr_text = f"{base_url}welcomeKit/{userID}/"  # Update URL as needed
    qr_image = qrcode.make(qr_text)

    # Save the QR code to a BytesIO object
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_code_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Add the QR code image to the registration object for rendering
    qr_code = qr_code_image

    context = {
        'qr': qr_code,
        'userType': userProfile.get_user_type_display(),
        'paymentCompleted': paymentCompleted,
        'paymentObservations': paymentObservations,
        'uploadFiles': uploadFiles,  # Cambiado para pasar todos los archivos subidos
        'isRejected': isRejected,
        'form': form,  # Pass the form to the template
        'is_staff_user': is_staff_user,
        'is_staff_superuser': is_staff_superuser,
    }
    return render(request, 'payments.html', context=context)

@staff_member_required
@completedProfileRequired
def scholarshipAssignations(request):
    profiles = UserProfile.objects.select_related('user').all()

    if request.method == 'POST':
        for profile in profiles:
            becado = request.POST.get(f"becado_{profile.id}", "off") == "on"
            profile.permitirRegistro = becado
            profile.save()
        return redirect('scholarshipAssignations')

    context = {
        'profiles': profiles
    }
    return render(request, 'scholarshipAssignations.html', context)

@login_required(login_url='google_login')
@completedProfileRequired
def schedule(request):
    userID = request.user.id
    

    userProfile = UserProfile.objects.get(user_id=userID)
    paymentCompleted = userProfile.payment_completed
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    allowRegistration = userProfile.permitirRegistro

    places = Place.objects.all()
    congress_dates = CongressDate.objects.filter(is_active=True)
    events_by_date = {}

    # Recopilar todas las horas de inicio y fin de los eventos
    all_events = Event.objects.all()
    
    # Crear un conjunto para los time slots
    time_slots_set = set()

    for event in all_events:
        if event.date in congress_dates.values_list('date', flat=True):
            # Agregar el inicio y fin del evento al conjunto
            time_slots_set.add(event.start_time)
            time_slots_set.add(event.end_time)

    # Generar time slots a partir de las horas de inicio y fin de los eventos
    time_slots = sorted(list(time_slots_set))

    # Crear un diccionario para eventos por fecha y slot de tiempo
    for date in congress_dates:
        events_by_date[date.date] = {slot: {place.name: [] for place in places} for slot in time_slots}

    for event in all_events:
        if event.date in events_by_date:
            event_start = event.start_time
            event_end = event.end_time
            
            for start_time in time_slots:
                # Añadir eventos a los slots correspondientes
                if event_start == start_time or (event_start < start_time < event_end):
                    # Calcula el número de usuarios registrados para cada evento
                    registered_users_count = Registration.objects.filter(event=event).count()
                    event.available_capacity = event.place.capacity - registered_users_count
                    events_by_date[event.date][start_time][event.place.name].append(event)

    # Limpiar los slots para que sean continuos
    final_time_slots = []
    last_slot = None
    
    for slot in time_slots:
        if last_slot is None or slot != last_slot:
            final_time_slots.append(slot)
            last_slot = slot

    # Validar si el usuario está registrado en un evento de todo el congreso (allEvent)
    user_registrations = set()
    user_has_full_event = False
    if request.user.is_authenticated:
        # Obtener eventos en los que el usuario está registrado
        user_registrations = set(Registration.objects.filter(user=request.user).values_list('event__title', flat=True))

        # Verificar si el usuario está registrado en un workshop de todo el evento (allEvent)
        user_has_full_event = Registration.objects.filter(user=request.user, event__allEvent=True).exists()
    
    # Obtener todos los registros para validación de conflictos de horario
    user_registrations_for_validation = list(Registration.objects.filter(user=request.user).values(
        'event__title', 
        'event__date', 
        'event__start_time', 
        'event__end_time'
    ))
    user_registrations = set(Registration.objects.filter(user=request.user).values_list('event__title', flat=True))


    context = {
        'allowRegistration': allowRegistration,
        'paymentCompleted': paymentCompleted,
        'events_by_date': events_by_date,
        'time_slots': time_slots,
        'places': places,
        'congress_dates': congress_dates,
        'user_registrations': list(user_registrations),
        'user_registrations_new': list(user_registrations_for_validation),
        'user_has_full_event': user_has_full_event,  # Se añade la variable al contexto
        'is_staff_user': is_staff_user,
        'is_staff_superuser': is_staff_superuser,
    }
    return render(request, 'schedule.html', context=context)


def schedulePublic(request):
    userID = request.user.id
    # userProfile = UserProfile.objects.get(user_id=userID)
    paymentCompleted = False
    # is_staff_user = request.user.is_staff  # This will be True or False
    # is_staff_superuser = request.user.is_superuser  # This will be True or False

    places = Place.objects.all()
    congress_dates = CongressDate.objects.filter(is_active=True)
    events_by_date = {}

    # Recopilar todas las horas de inicio y fin de los eventos
    all_events = Event.objects.all()
    
    # Crear un conjunto para los time slots
    time_slots_set = set()

    for event in all_events:
        if event.date in congress_dates.values_list('date', flat=True):
            # Agregar el inicio y fin del evento al conjunto
            time_slots_set.add(event.start_time)
            time_slots_set.add(event.end_time)

    # Generar time slots a partir de las horas de inicio y fin de los eventos
    time_slots = sorted(list(time_slots_set))

    # Crear un diccionario para eventos por fecha y slot de tiempo
    for date in congress_dates:
        events_by_date[date.date] = {slot: {place.name: [] for place in places} for slot in time_slots}

    for event in all_events:
        if event.date in events_by_date:
            event_start = event.start_time
            event_end = event.end_time
            
            for start_time in time_slots:
                # Añadir eventos a los slots correspondientes
                if event_start == start_time or (event_start < start_time < event_end):
                    # Calcula el número de usuarios registrados para cada evento
                    registered_users_count = Registration.objects.filter(event=event).count()
                    event.available_capacity = event.place.capacity - registered_users_count
                    events_by_date[event.date][start_time][event.place.name].append(event)

    # Limpiar los slots para que sean continuos
    final_time_slots = []
    last_slot = None
    
    for slot in time_slots:
        if last_slot is None or slot != last_slot:
            final_time_slots.append(slot)
            last_slot = slot

    

    context = {
        'paymentCompleted': paymentCompleted,
        'events_by_date': events_by_date,
        'time_slots': time_slots,
        'places': places,
        'congress_dates': congress_dates,
        # 'user_registrations': list(user_registrations),
        # 'user_has_workshop': user_has_workshop,
        # 'is_staff_user': is_staff_user,
        # 'is_staff_superuser':is_staff_superuser,
    }
    return render(request, 'schedulePublic.html', context=context)

@login_required
def validPay(request):
    txn_id = request.GET.get('PayerID')
    userID = request.user.id
    userProfile = UserProfile.objects.get(user_id=userID)
    userProfile.transactionID=txn_id
    userProfile.payment_completed=True
    userProfile.save()
    return redirect('payment')

@login_required
def register_place(request):
    if request.method == 'POST':
        form = PlaceForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new place to the database
            return redirect('schedule')  # Redirect to the schedule or another page
    else:
        form = PlaceForm()
    
    return render(request, 'registerPlace.html', {'form': form})

@login_required
@require_POST
def registerintoEvent(request):
    event_title = request.POST.get('event_title')
    try:
        # Obtener todos los eventos por título
        events = Event.objects.filter(title=event_title)

        # Comprobar si hay eventos encontrados
        if not events.exists():
            return JsonResponse({'success': False, 'error': 'Event not found'})

        user = request.user

        # Obtener todos los registros del usuario
        user_registrations = Registration.objects.filter(user=user).select_related('event')

        # Verificar si el usuario ya está registrado en algún evento con el mismo título
        registered_events = user_registrations.filter(event__title=event_title)
        if registered_events.exists():
            return JsonResponse({'success': False, 'error': 'You are already registered for one of these events'})

        # Verificar conflictos de horario
        conflicting_registrations = user_registrations.filter(
            Q(event__date__in=events.values_list('date', flat=True)) &
            (
                Q(event__start_time__lt=events.values_list('end_time', flat=True)) &
                Q(event__end_time__gt=events.values_list('start_time', flat=True))
            )
        )

        if conflicting_registrations.exists():
            return JsonResponse({'success': False, 'error': 'You cannot register for events with overlapping times'})
        
        for event in events:
            current_registrations = Registration.objects.filter(event=event).count()
            if current_registrations >= event.place.capacity:
                return JsonResponse({'success': False, 'error': f'No space available for the event: {event.title}'})

        # Registrar al usuario para cada evento encontrado
        for event in events:
            Registration.objects.create(user=user, event=event)

        return JsonResponse({'success': True})

    except IntegrityError:
        return JsonResponse({'success': False, 'error': 'You are already registered for one of these events'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def register_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()  # No es necesario usar commit=False aquí
            return redirect('schedule')
    else:
        form = EventForm()
    
    return render(request, 'registerEvent.html', {'form': form})

@staff_member_required
def list_events(request):
    events = Event.objects.all()  # Get all event objects
    return render(request, 'listEvents.html', {'events': events})

@staff_member_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)  # Fetch the event object by ID

    if request.method == 'POST':
        event.delete()  # Delete the event
        messages.success(request, 'Event deleted successfully.')
        return redirect('listEvents')  # Redirect to the event list page

    return render(request, 'confirmDeleteEvent.html', {'event': event})

@staff_member_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)  # Añade request.FILES aquí
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('schedule')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'editEvent.html', {'form': form, 'event': event})


@staff_member_required
def manage_congress_dates(request):
    congress_dates = CongressDate.objects.all().order_by('date')
    
    if request.method == 'POST':
        form = CongressDateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Congress date added successfully.')
            return redirect('manageCongressDates')
    else:
        form = CongressDateForm()

    return render(request, 'manageCongressDates.html', {'form': form, 'congress_dates': congress_dates})

@staff_member_required
def edit_congress_date(request, date_id):
    congress_date = get_object_or_404(CongressDate, id=date_id)
    
    if request.method == 'POST':
        form = CongressDateForm(request.POST, instance=congress_date)
        if form.is_valid():
            form.save()
            messages.success(request, 'Congress date updated successfully.')
            return redirect('manageCongressDates')
    else:
        form = CongressDateForm(instance=congress_date)

    return render(request, 'editCongressDate.html', {'form': form, 'congress_date': congress_date})

@staff_member_required
def delete_congress_date(request, date_id):
    congress_date = get_object_or_404(CongressDate, id=date_id)
    
    if request.method == 'POST':
        congress_date.delete()
        messages.success(request, 'Congress date deleted successfully.')
        return redirect('manageCongressDates')

    return render(request, 'deleteCongressDate.html', {'congress_date': congress_date})


@login_required
@completedProfileRequired
def seeMySchedule(request):
    userID = request.user.id
    userProfile = UserProfile.objects.get(user_id=userID)
    paymentCompleted = userProfile.payment_completed
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    registrations = Registration.objects.filter(user=userID).select_related('event')
    base_url = f"{request.scheme}://{request.get_host()}/"
    # Generate QR codes for each registration
    registrations = Registration.objects.filter(user=userID).select_related('event')
    base_url = f"{request.scheme}://{request.get_host()}/"
    # Generate QR codes for each registration
    for registration in registrations:
        qr_text = f"{base_url}assist/{userID}/{registration.pk}"  # Update URL as needed
        qr_image = qrcode.make(qr_text)


        # Save the QR code to a BytesIO object
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Add the QR code image to the registration object for rendering
        registration.qr_code = qr_code_image
        registration.event_link = registration.event.links


    context={
        'paymentCompleted':paymentCompleted,
        'registrations': registrations,
        'is_staff_user': is_staff_user,
        'is_staff_superuser':is_staff_superuser,
        # 'consolidated_list':consolidated_list,
    }
    
    return render(request,'seeMySchedule.html',context)

@staff_member_required
def assistanceControl(request, user_id, registration_id):
    # Get the registration object based on the user and registration IDs
    registration = get_object_or_404(Registration, user_id=user_id, id=registration_id)
    
    # Update the assisted field to True
    registration.assisted = True
    registration.counter = registration.counter + 1
    registration.save()
    
    # Optionally, redirect to a success page or back to the registration list
    return redirect('dashboard')  # Replace with your desired redirect URL

@staff_member_required
def welcomeKit(request, user_id):
    # Obtén el objeto de perfil del usuario según su ID
    registration = get_object_or_404(UserProfile, user_id=user_id)
    
    # Verifica si el kit ya ha sido recibido
    if  registration.recibioKIT:
        # Redirige a una vista que indica que ya ha recibido el kit
        return redirect('kitAlreadyReceived')  
    else:
        # Si no se ha recibido, actualiza el campo a True
        registration.recibioKIT = True
        registration.save()
        # Redirige a una vista que confirma que se registró el recibo del kit
        return redirect('kitReceivedSuccessfully')  
@staff_member_required
def kitReceivedSuccessfully(request):
    return render(request,'kitReceivedSuccessfully.html')
@staff_member_required
def kitAlreadyReceived(request):
    return render(request,'kitAlreadyReceived.html')

@staff_member_required
def listarRecibioKit(request):
    users = UserProfile.objects.all()
    saved = False
    
    if request.method == "POST":
        # Primero, establecemos todos los usuarios como no recibidos
        UserProfile.objects.update(recibioKIT=False)
        
        # Luego, procesamos los datos enviados
        for key, value in request.POST.items():
            if key.startswith('user_status['):
                user_id = key[12:-1]  # Extraer el ID del usuario
                received_kit = (value == 'on')
                
                try:
                    user_profile = UserProfile.objects.get(id=user_id)
                    user_profile.recibioKIT = received_kit
                    user_profile.save()
                except UserProfile.DoesNotExist:
                    # Manejar el caso en que el perfil de usuario no existe
                    pass
        
        saved = True
        return redirect('consultWelcomeKit')

    return render(request, 'registroKits.html', {'users': users, 'saved': saved})

@staff_member_required
def assistanceList(request):
    registrations = Registration.objects.select_related('event', 'user')  # Fetch all registrations with related event and user info
    context={
        'registrations': registrations,
    }
    return render(request,'assitanceList.html',context)

@staff_member_required
def validatePayment(request):
    user_profiles = UserProfile.objects.select_related('user').prefetch_related('paymentproof_set').all()

    # Get the social accounts for all users in the user profiles
    social_accounts = SocialAccount.objects.filter(user__in=[profile.user for profile in user_profiles])

    # Create a dictionary to map user_id to their extra_data (JSON field)
    social_extra_data = {account.user_id: account.extra_data for account in social_accounts}

    if request.method == 'POST':
        for user_profile in user_profiles:
            # Get the value of payment_completed checkbox
            payment_completed = request.POST.get(f'payment_completed_{user_profile.user.id}') == 'on'
            user_profile.payment_completed = payment_completed
            
            # Get the value of manualPayment checkbox
            manual_payment = request.POST.get(f'manual_payment_{user_profile.user.id}') == 'on'
            user_profile.manualPayment = manual_payment
            
            # Get the amount value and convert it to a float (or decimal, as needed)
            amount = request.POST.get(f'amount_{user_profile.user.id}')
            if amount:
                try:
                    user_profile.amount = float(amount)  # Use Decimal if needed
                except ValueError:
                    user_profile.amount = 0.0  # Default to 0 if conversion fails
            
            # Save the updated user profile
            user_profile.save()
        
        return redirect('validatePaymentAdmin')

    # Pass user profiles and the social account data (extra_data) to the template
    context = {
        'user_profiles': user_profiles,
        'social_extra_data': social_extra_data,  # Passing the social account data to the template
    }
    return render(request, 'validatePayment.html', context)



@staff_member_required
def registerStaff(request):
    
    is_staff_user=request.user.is_staff
    is_staff_superuser=request.user.is_superuser
    if is_staff_superuser:
        users = CustomUser.objects.all()        
        social_accounts = SocialAccount.objects.filter(user__in=users)
        social_extra_data = {account.user_id: account.extra_data for account in social_accounts}
        if request.method == 'POST':
            # Process form submission to update staff status
            for user in users:
                is_staff = request.POST.get(f'is_staff_{user.id}') == 'on'
                user.is_staff = is_staff
                user.save()

            return redirect('registerStaff')  
        context={
            'is_staff_user':is_staff_user,
            'is_staff_superuser':is_staff_superuser,
            'users': users,
            'social_extra_data': social_extra_data,  # Passing the social account data to the template
        }
        return render(request,'registerStaff.html',context)
    else:
        return redirect('dashboard')
    

@login_required
@completedProfileRequired
def seeMyDiplomas(request):
    is_staff_user = request.user.is_staff
    is_staff_superuser = request.user.is_superuser
    registrations = Registration.objects.filter(user=request.user.id).select_related('event')

    # Diccionario para consolidar eventos por título
    consolidated_events = defaultdict(lambda: {
        "date": None,
        "start_time": None,
        "end_time": None,
        "registration": None  # Para almacenar el registro que tenga el botón (el del evento más tardío)
    })

    for registration in registrations:
        event_title = registration.event.title

        # Consolidar la hora de inicio más temprana y la hora de término más tardía
        if (consolidated_events[event_title]["start_time"] is None or 
            registration.event.start_time < consolidated_events[event_title]["start_time"]):
            consolidated_events[event_title]["start_time"] = registration.event.start_time
            consolidated_events[event_title]["date"] = registration.event.date  # Asumir que la fecha es la misma para todos los bloques

        if (consolidated_events[event_title]["end_time"] is None or 
            registration.event.end_time > consolidated_events[event_title]["end_time"]):
            consolidated_events[event_title]["end_time"] = registration.event.end_time
            consolidated_events[event_title]["registration"] = registration  # Guardar el registro del evento más tardío

    # Preparar la lista de eventos consolidados para pasarla al template
    consolidated_list = [
        {
            "title": title,
            "date": details["date"],
            "start_time": details["start_time"],
            "end_time": details["end_time"],
            "registration": details["registration"]
        }
        for title, details in consolidated_events.items()
    ]

    context = {
        'is_staff_user': is_staff_user,
        'is_staff_superuser': is_staff_superuser,
        'registrations': consolidated_list,
    }
    return render(request, 'seeMyDiplomas.html', context)

@login_required(login_url='accounts/google/')
def generateMyDiplomas(request,event_id):
    eventInformation = Event.objects.get(id=event_id)
    lastAllEvent=eventInformation.allEvent
    cargaInscripcion=Registration.objects.get(event_id=event_id,user_id=request.user.id)
    allowDiploma=False

    if lastAllEvent:
        asisted=cargaInscripcion.assisted
        counterAssistance=cargaInscripcion.counter
        if counterAssistance<3:
            allowDiploma=False
    else:
        asisted=cargaInscripcion.assisted
        
        if asisted:
            allowDiploma=True
        
        


    eventFilePath=eventInformation.fileDiplomas
    userInformation=UserProfile.objects.get(user_id=request.user.id)
    name=userInformation.FullName
    if name is None or name.strip() == "":
        name = "Participant"
    
    email=SocialAccount.objects.get(user_id=request.user.id).extra_data.get('email')
    # print(email)
    # email=userInformation.user.email
    
    subject = "International Conference on Software Process Improvement CIMPS"
    body = """ ================= THANK YOU<br> Attached to this email you will find your corresponding diploma for you atendance to CIMPS <br> =================<br><br>Warm regards,JMM<br>CIMPS Chair <br>"""

    def create_diploma(template_path, name, output_image_path):
        # Abrir la plantilla de imagen
        image = Image.open(template_path)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        draw = ImageDraw.Draw(image)

        font_url = "https://github.com/Outfitio/Outfit-Fonts/raw/refs/heads/main/fonts/ttf/Outfit-Regular.ttf"
        # Configurar la fuente
        try:
            response = requests.get(font_url)
            font = ImageFont.truetype(BytesIO(response.content), 180)
            
        except:
            print("No se pudo cargar la fuente")
            font = ImageFont.load_default()
            text_bbox = draw.textbbox((0, 0), name, font=font)
            default_text_width = text_bbox[2] - text_bbox[0]
            default_text_height = text_bbox[3] - text_bbox[1]
        

        # Obtener tamaño del texto usando la fuente
        text_bbox = draw.textbbox((0, 0), name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        width, height = image.size
        

        # Posicionar el texto en el centro de la imagen
        x = (width - text_width) / 2
        y = (height - text_height) / 2  # Centrar el texto verticalmente también
        if font == ImageFont.load_default():
            # If we're using the default font, we need to scale the image up before drawing
            # and then scale it back down to get a larger text
            large_image = image.resize((int(width * scale_factor), int(height * scale_factor)), Image.LANCZOS)
            large_draw = ImageDraw.Draw(large_image)
            large_x = (large_image.width - text_width * scale_factor) / 2
            large_y = (large_image.height - text_height * scale_factor) / 2
            large_draw.text((large_x, large_y), name, font=font, fill="black")
            image = large_image.resize((width, height), Image.LANCZOS)
        else:
            draw.text((x, y), name, font=font, fill="black")

        # Añadir el nombre al diploma
        # draw.text((x, y), name, font=font, fill="black")

        # Guardar la imagen con el nombre del diploma
        image.save(output_image_path,'JPEG')
    def create_protected_pdf(image_path, pdf_path, owner_password):
        # Crear un PDF a partir de la imagen
        c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
        c.drawImage(image_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1])
        c.save()
        
        # Proteger el PDF con contraseña
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # Permitir abrir el archivo sin contraseña, pero protegerlo contra edición
        writer.encrypt(user_pwd="", owner_pwd=owner_password, use_128bit=True)
        
        with open(pdf_path, "wb") as f:
            writer.write(f)

    def send_email(receiver_email, subject, body, pdf_path):
        sender = "conferencecimps@cimat.mx"
        password = "HIPOCRATES@2022"

        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "html"))

        with open(pdf_path, "rb") as f:
            attach = MIMEApplication(f.read(),_subtype="pdf")
            attach.add_header('Content-Disposition','attachment',filename=os.path.basename(pdf_path))
            message.attach(attach)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(message)

    # eventFilePath
    if cargaInscripcion.assisted is False:
        messages.error(request, "You have not assisted in this event. Please register your assistance through the QR scanner with a staff member if required.")
        allowDiploma = False


    if not eventInformation.is_ready_for_certificate() or  cargaInscripcion.receivedDiploma is True:
        allowDiploma = False
        messages.error(request, "You have already received your certificate. You can't receive it again.")
    output_folder = "./static/diplomas"
    if not eventInformation.is_ready_for_certificate() or allowDiploma is False:

        messages.error(request, "The event is not ready for this certificate, check the date and hours of the event. Also make sure that your assistance is registered through the QR scanner with a staff member. If you do not register your assistance in time, you will not be able to receive the certificate. Is possible that you already received this certificate.")
        return redirect('seeMyDiplomas')
    elif eventInformation.is_ready_for_certificate() and allowDiploma is True:
        os.makedirs(output_folder, exist_ok=True)
        image_path = os.path.join(output_folder,  f"{name}.jpg")
        create_diploma(eventFilePath, name, image_path)
        pdf_path=os.path.join(output_folder,  f"{name}.pdf")
        owner_password="Cimps2025.Terron456#@!"
        create_protected_pdf(image_path,pdf_path,owner_password)

        send_email(email,subject,body,pdf_path)
        cargaInscripcion.receivedDiploma=True
        cargaInscripcion.save()
        messages.success(request, "The diploma is already in your inbox! Check your email, in case of issues contact: victor.terron@cimat.mx")  # Agrega un mensaje de éxito
    else:
        messages.error(request, "Error! Check your contact: victor.terron@cimat.mx describing your issue")
    
    return redirect('seeMyDiplomas')



#PARA SUBIR IMAGENES AL BANNER
@login_required(login_url='google_login')
@superuser_required
def upload_banner(request):
    banners_path = os.path.join(settings.BASE_DIR, 'mainApplication', 'static', 'images', 'banners')
    os.makedirs(banners_path, exist_ok=True)  # Crear el directorio si no existe
    files = os.listdir(banners_path)
    file_list = [{'name': file, 'url': os.path.join('images', 'banners', file)} for file in files]

    if request.method == 'POST' and request.FILES['banner']:
        banner_file = request.FILES['banner']
        
        # Ruta destino (definida directamente)
        banners_path = os.path.join(settings.BASE_DIR, 'mainApplication', 'static', 'images', 'banners')
        os.makedirs(banners_path, exist_ok=True)  # Crear el directorio si no existe

        # Guardar archivo
        fs = FileSystemStorage(location=banners_path)
        filename = fs.save(banner_file.name, banner_file)
        file_url = os.path.join('static', 'images', 'banners', filename)
        
        # return JsonResponse({'message': 'Archivo subido exitosamente', 'file_url': file_url})
    context={
        'registrations':file_list
    }

    return render(request, 'upload_banner.html',context)

@login_required(login_url='google_login')
@superuser_required
def delete_file(request, filename):
    # Construir la ruta completa del archivo
    banners_path = os.path.join(settings.BASE_DIR, 'mainApplication', 'static', 'images', 'banners')
    file_path = os.path.join(banners_path, filename)

    # Verificar si el archivo existe
    if os.path.exists(file_path):
        os.remove(file_path)  # Eliminar el archivo
    else:
        return HttpResponseNotFound("El archivo no existe.")  # Manejar error si no se encuentra el archivo

    # Redirigir a la página de subir banners
    return redirect('upload_banner')

#FOR EDITING HTE TOPICS THAT ADDRESSES THE CONFERENCE
@superuser_required
def topics(request):
    topics = TopicArea.objects.all()
    if request.method == 'POST':
        form = TopicAreaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('topicsArea')
    else:
        form = TopicAreaForm()
    context = {
        'topics': topics,
        'form': form
    }
    return render(request, 'topicArea.html', context)

@superuser_required
def deleteTopics(request,pk):
    topic = TopicArea.objects.get(id=pk)
    topic.delete()
    return redirect('topicsArea')

@superuser_required
def editTopic(request,pk):
    # topic = TopicArea.objects.get(id=pk)
    topic = get_object_or_404(TopicArea, id=pk)

    if request.method == 'POST':
        form = TopicAreaForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            return redirect('topicsArea')
    else:
        form = TopicAreaForm(instance=topic)
    context = {
        'form': form
    }
    return render(request, 'editTopic.html', context)


@login_required(login_url='google_login')
@completedProfileRequired
def submitArticle(request,submission_id=None):
    AuthorFormSet = formset_factory(AuthorForm, extra=1)  # Allows adding multiple authors

    submission = None#si editamos una submission existente
    if submission_id:
        submission = get_object_or_404(Submission, id=submission_id, user=request.user)


    if request.method == 'POST':
        submission_form = SubmissionForm(request.POST)
        author_formset = AuthorFormSet(request.POST, prefix='authors')
        file_form = SubmissionFileForm(request.POST, request.FILES)

        # Determine if the user clicked "Save Draft" or "Submit"
        is_submit = "submit" in request.POST
        is_save_draft = "save_draft" in request.POST

        if submission_form.is_valid() and author_formset.is_valid() and file_form.is_valid():
            # Save the submission
            submission = submission_form.save(commit=False)
            submission.user = request.user
            submission.sent_for_review = is_submit  # Only mark as submitted if "Submit" was clicked
            submission.save()
            submission_form.save_m2m()  # Save M2M fields like topic_areas

            # Save authors
            for author_form in author_formset:
                if author_form.cleaned_data:  # Avoid saving empty forms
                    author = author_form.save(commit=False)
                    author.submission = submission
                    author.save()

            # Save multiple files
            files = request.FILES.getlist('files')  # Matches the 'files' field in the form
            for file in files:
                SubmissionFile.objects.create(submission=submission, file=file)

            # Show success messages
            if is_submit:
                messages.success(request, 'Article submitted successfully.')
            elif is_save_draft:
                messages.success(request, 'Draft saved successfully.')

            messages.success(request, 'Article submitted successfully.')
            return redirect('seeMySubmissions')  # Replace with your desired redirect
    else:
        submission_form = SubmissionForm(instance=submission)
        author_formset = AuthorFormSet(prefix='authors')
        file_form = SubmissionFileForm(submission=submission)

    existing_files = []
    if submission:
        existing_files = submission.files.all()

    return render(request, 'makeSubmission.html', {
        'submission_form': submission_form,
        'author_formset': author_formset,
        'file_form': file_form,
        'existing_files': existing_files,
        'submission': submission,
    })


@login_required(login_url='google_login')
@completedProfileRequired
def seeMySubmissions(request):
    submissions = Submission.objects.filter(user_id=request.user.id,is_withdrawn=False)
    
    context={
        'submissions': submissions,
    }
    return render(request, 'mySubmissions.html',context)


@login_required
@completedProfileRequired
def editSubmission(request, submissionID):
    # Cambiamos extra=0 a extra=1 para permitir un nuevo formulario en blanco
    AuthorFormSet = formset_factory(AuthorForm, extra=0, can_delete=True)
    submission = get_object_or_404(Submission, submission_id=submissionID, user=request.user)
    
    if request.user.id is not submission.user_id:
        return redirect('seeMySubmissions')
    
    if request.method == 'POST':
        is_submit = "submit" in request.POST
        

        submission_form = SubmissionForm(request.POST, instance=submission)
        author_formset = AuthorFormSet(request.POST, prefix='authors')
        file_form = SubmissionFileForm(request.POST, request.FILES)


        if submission_form.is_valid() and author_formset.is_valid() and file_form.is_valid():
            
            
                
            # Save the submission
            submission = submission_form.save(commit=False)
            if is_submit:  # If the submit button was pressed
                submission.sent_for_review = True  # Mark as sent for review
            submission.save()
            submission_form.save_m2m()

            # Handle authors - modificamos esta parte para manejar eliminaciones
            submission.authors.all().delete()
            for author_form in author_formset:
                if author_form.cleaned_data and not author_form.cleaned_data.get('DELETE', False):
                    author = author_form.save(commit=False)
                    author.submission = submission
                    author.save()

            # Handle files
            if request.FILES.getlist('files'):
                for file in request.FILES.getlist('files'):
                    SubmissionFile.objects.create(submission=submission, file=file)

            messages.success(request, 'Submission updated successfully.')
            return HttpResponseRedirect(request.path)
        

    else:
        submission_form = SubmissionForm(instance=submission)
        author_formset = AuthorFormSet(
            prefix='authors',
            initial=[{
                'honorific': author.honorific,
                'first_name': author.first_name,
                'last_name': author.last_name,
                'position_title': author.position_title,
                'organization': author.organization,
                'department': author.department,
                'address': author.address,
                'city': author.city,
                'state_province': author.state_province,
                'postcode_zip': author.postcode_zip,
                'email': author.email,
            } for author in submission.authors.all()]
        )
        file_form = SubmissionFileForm()

    existing_files = submission.files.all()

    return render(request, 'editSubmission.html', {
        'submission_form': submission_form,
        'author_formset': author_formset,
        'file_form': file_form,
        'existing_files': existing_files,
        'submission': submission,
    })


@require_POST
def delete_file(request, file_id):
    try:
        file = SubmissionFile.objects.get(id=file_id)
        file.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
def withdraw_submission(request, submission_id):
    submission = get_object_or_404(Submission, submission_id=submission_id)

    # Verifica si el usuario es el propietario del artículo
    if submission.user != request.user:
        messages.error(request, "You don't have permission to withdraw this article.")
        return redirect('seeMySubmissions')  # Cambia 'some_view_name' por la vista que corresponde.

    # Cambia el estado o agrega una lógica para indicar que está retirado.
    submission.sent_for_review = False
    submission.under_review = False
    submission.decision_issued = False
    submission.is_withdrawn = True
    submission.save()

    messages.success(request, "The article has been successfully withdrawn.")
    return redirect('seeMySubmissions')  # Cambia 'some_view_name' por la vista correspondiente.

def validate_email_list(email_list):
    """Helper function to validate a list of email addresses"""
    valid_emails = []
    invalid_emails = []

    for email in email_list:
        email = email.strip()  # Remove extra spaces
        try:
            # Use Django's built-in email validator
            validate_email(email)
            valid_emails.append(email)
        except ValidationError:
            invalid_emails.append(email)

    return valid_emails, invalid_emails

@superuser_required
@completedProfileRequired
def inviteReviewers(request):
    """
    Handles both rendering the invitation form and sending email invitations to reviewers.
    """
    if request.method == 'POST':
        # Extract data from the form
        subject = request.POST.get('subject')
        body_template = request.POST.get('message') + " <br> Please click here: <a href='{url}'>Become a Reviewer</a> <br> If this email is not a Gmail account, is mandatory to create one to access the platform. Then to become a reviewer in your profile section add the following code: {hashedEmail}."
        bcc = request.POST.get('bcc')  # Comma-separated email addresses
        base_url = f"{request.scheme}://{request.get_host()}/becomeReviewer"

        # Process recipient list
        bcc_list = [email.strip() for email in bcc.split(',')]
        valid_bcc, invalid_bcc = validate_email_list(bcc_list)

        if invalid_bcc:
            messages.error(request, f"The following emails are invalid: {', '.join(invalid_bcc)}")
            return redirect('inviteReviewers')  # Redirect back with an error

        # Email sending logic
        sender = "conferencecimps@cimat.mx"
        password = "HIPOCRATES@2022"

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender, password)
                for recipient in bcc_list:
                    # Generate SHA-256 hash for the email
                    hashed_email = hashlib.sha256(recipient.encode()).hexdigest()
                    personalized_url = f"{base_url}/{hashed_email}"

                    # Format the email body
                    body = body_template.format(url=personalized_url,hashedEmail=hashed_email)

                    # Create the email message
                    message = MIMEMultipart()
                    message["From"] = sender
                    message["To"] = recipient
                    message["Subject"] = subject
                    message.attach(MIMEText(body, "html"))

                    # Send the email
                    server.send_message(message)
                    try:
                        reviewersCodes.objects.create(code=hashed_email,email=recipient)
                    except:
                        pass

            messages.success(request, 'Emails sent successfully!')
        except Exception as e:
            messages.error(request, f'Error sending emails: {str(e)}')

        # Redirect back to the form page
        return redirect('inviteReviewers')  # Update this to match your URL name

    context={
        'reviewers':reviewersCodes.objects.all()
    }
    return render(request, 'inviteReviewers.html',context)

@login_required(login_url='google_login')
@completedProfileRequired
def becomeReviewer(request, code_hash):
    # Find the code associated with the hashed email
    code_obj = get_object_or_404(reviewersCodes, code=code_hash)

    # Check if the user is already associated with the code (if not already accepted)
    if not code_obj.user:
        # Populate the user field with the currently logged-in user
        code_obj.user = request.user
        code_obj.used = True  # Mark as used (accepted)
        code_obj.save()

        # Optionally, set the user as a reviewer if that's required
        request.user.isReviewer = True
        request.user.save()

        messages.success(request, 'You have successfully become a reviewer.')


        # Redirect or display a success message
        return redirect('dashboard')  # Redirect to some page after accepting the invitation
    else:
        messages.error(request, 'The invitation has already been accepted.')

        # Handle the case where the invitation has already been accepted (optional)
        return redirect('dashboard')  # Or display an error message
    
@superuser_required
def assignReviews(request):
    reviewers = CustomUser.objects.filter(isReviewer=True)
    submissions = Submission.objects.filter(
        sent_for_review=True,
        is_withdrawn=False
    ).prefetch_related('reviewers')

    if request.method == 'POST':
        # Dictionary to store reviewer assignments
        reviewer_assignments = defaultdict(list)
        
        # Process the form data
        for submission in submissions:
            # Get list of selected reviewers for this submission
            new_reviewer_ids = request.POST.getlist(f'reviewers_{submission.id}')
            
            # Get current reviewers for comparison
            current_reviewer_ids = set(str(rid) for rid in submission.reviewers.values_list('id', flat=True))
            new_reviewer_ids_set = set(new_reviewer_ids)
            
            # Determine which reviewers to add and remove
            reviewers_to_add = new_reviewer_ids_set - current_reviewer_ids
            reviewers_to_remove = current_reviewer_ids - new_reviewer_ids_set
            
            # Remove unselected reviewers
            for reviewer_id in reviewers_to_remove:
                submission.reviewers.remove(reviewer_id)
            
            # Add new reviewers and prepare notifications
            for reviewer_id in reviewers_to_add:
                reviewer = CustomUser.objects.get(id=reviewer_id)
                submission.reviewers.add(reviewer)
                reviewer_assignments[reviewer_id].append(submission)
            
            # Update submission status if it has any reviewers
            submission.assigned_reviewers = bool(new_reviewer_ids)
            submission.save()
        
        # Send email notifications only to newly assigned reviewers
        if reviewer_assignments:
            sender = "conferencecimps@cimat.mx"
            password = "HIPOCRATES@2022"
            
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(sender, password)
                    
                    # Send emails to reviewers
                    for reviewer_id, assigned_submissions in reviewer_assignments.items():
                        reviewer = CustomUser.objects.get(id=reviewer_id)
                        
                        # Create submission list for email
                        submissions_list = "<br>".join([
                            f"- {submission.title} (ID: {submission.submission_id})"
                            for submission in assigned_submissions
                        ])
                        
                        # Create email content
                        subject = "New Review Assignments"
                        body = f"""
                        Dear {reviewer.get_full_name() or reviewer.username},
                        <br><br>
                        The chair has assigned you the following articles to assess:
                        <br><br>
                        {submissions_list}
                        <br><br>
                        Please visit your dashboard to review these submissions.
                        <br><br>
                        Best regards,<br>
                        Conference Management System
                        """
                        
                        # Create the email message
                        message = MIMEMultipart()
                        message["From"] = sender
                        message["To"] = reviewer.email
                        message["Subject"] = subject
                        message.attach(MIMEText(body, "html"))
                        
                        # Send the email
                        server.send_message(message)
                
                messages.success(request, 'Review assignments have been updated successfully.')
                
            except Exception as e:
                messages.error(request, f'Error sending emails: {str(e)}')
        else:
            messages.success(request, 'Review assignments have been updated successfully.')
        
        return redirect('assignReviews')

    context={
        'reviewers': reviewers,
        'submissions': submissions,
    }
    return render(request, 'assignReviews.html',context)

@superuser_required
def revertToDraftStatus(request,submission_id):
    submissions = Submission.objects.filter(
        submission_id=submission_id,
    ).prefetch_related('reviewers')

    for submission in submissions:
        submission.reviewers.clear()  # This will remove all entries from submission_reviewers

        submission.sent_for_review = False
        submission.under_review = False
        submission.decision_issued = False
        submission.save()

    messages.success(request, 'All submissions have been reverted to draft status.')
    return redirect('assignReviews')

@superuser_required
def listSubmissions(request):
    submissions = Submission.objects.all().prefetch_related('reviewers')

    context={
        'submissions': submissions,
    }
    return render(request, 'listSubmissions.html',context)