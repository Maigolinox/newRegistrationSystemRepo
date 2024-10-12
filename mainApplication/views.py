import base64
from datetime import timedelta, datetime
import os
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import qrcode
from .forms import UserProfileForm,PaymentProofForm,EventForm, PlaceForm,CongressDateForm
from .models import UserProfile,PaymentProof,Place,CongressDate,Event,Registration
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django_countries import countries
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User

import pycountry
from io import BytesIO
from collections import defaultdict


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




# Create your views here.

def index(request):
    return render(request,'index.html')

@login_required
def dashboard(request):
    userID = request.user.id
    allowRegistration=False
    try:
        userProfile = UserProfile.objects.get(user_id=userID)
        paymentCompleted = userProfile.payment_completed
        allowRegistration = userProfile.permitirRegistro
        
        userType = userProfile.user_type
    except ObjectDoesNotExist:
        userProfile = None
        paymentCompleted = False  # Assuming no payment if no profile exists
        userType = "Uncompleted profile"

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

    # userProfile = UserProfile.objects.get(user_id=userID)
    # paymentCompleted = userProfile.payment_completed
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    try:
        userType=userProfile.user_type
    except:
        userType="Uncompleted profile"
    context = {
        'qr':qr_code,
        'allowRegistration':allowRegistration,
        'paymentCompleted': paymentCompleted,
        'userType':userProfile,
        'is_staff_user': is_staff_user,
        'is_staff_superuser':is_staff_superuser,
    }
    return render(request,'dashboard.html',context)

@login_required
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


@login_required
def payment(request):
    userID = request.user.id
    try:
        userProfile = UserProfile.objects.get(user_id=userID)
        paymentObservations = userProfile.payment_completed
        paymentCompleted = userProfile.payment_completed
    except:
        return redirect('complete_profile')
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

from itertools import groupby
from operator import attrgetter


@staff_member_required
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

@login_required
def schedule(request):
    userID = request.user.id
    try:
        userProfile = UserProfile.objects.get(user_id=userID)
    except:
        return redirect('complete_profile')

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
def seeMySchedule(request):
    userID = request.user.id
    try:
        userProfile = UserProfile.objects.get(user_id=userID)
    except:
        return redirect('complete_profile')
    userProfile = UserProfile.objects.get(user_id=userID)
    paymentCompleted = userProfile.payment_completed
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
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


    context={
        'paymentCompleted':paymentCompleted,
        'registrations': registrations,
        'is_staff_user': is_staff_user,
        'is_staff_superuser':is_staff_superuser,
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
        users = User.objects.all()        
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
def seeMyDiplomas(request):
    is_staff_user=request.user.is_staff
    is_staff_superuser=request.user.is_superuser
    registrations = Registration.objects.filter(user=request.user.id).select_related('event')

    

    context={
        'is_staff_user':is_staff_user,
        'is_staff_superuser':is_staff_superuser,
        'registrations': registrations,
    }
    return render(request,'seeMyDiplomas.html',context)

@login_required
def generateMyDiplomas(request,event_id):
    eventInformation = Event.objects.get(id=event_id)
    lastAllEvent=eventInformation.allEvent
    cargaInscripcion=Registration.objects.get(event_id=event_id,user_id=request.user.id)
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
    
    subject = "International Conference on Software Process Improvement CIMPS 2024"
    body = """ ================= THANK YOU<br> Attached to this email you will find your corresponding diploma for you atendance to CIMPS 2024<br> =================<br><br>Warm regards,JMM<br>CIMPS Chair <br>2024<br>"""

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
    output_folder = "./static/diplomas"
    if not eventInformation.is_ready_for_certificate() or allowDiploma is False:
        messages.error(request, "The event is not ready for this certificate, check the date and hours of the event. Also make sure that your assistance is registered through the QR scanner with a staff member. If you do not register your assistance in time, you will not be able to receive the certificate.")
        return redirect('seeMyDiplomas')
    elif eventInformation.is_ready_for_certificate() and allowDiploma is True:
        os.makedirs(output_folder, exist_ok=True)
        image_path = os.path.join(output_folder,  f"{name}.jpg")
        create_diploma(eventFilePath, name, image_path)
        pdf_path=os.path.join(output_folder,  f"{name}.pdf")
        owner_password="Cimps2024.Terron123#@!"
        create_protected_pdf(image_path,pdf_path,owner_password)

        send_email(email,subject,body,pdf_path)
        cargaInscripcion.receivedDiploma=True
        cargaInscripcion.save()
        messages.success(request, "The diploma is already in your inbox! Check your email, in case of issues contact: victor.terron@cimat.mx")  # Agrega un mensaje de éxito
    else:
        messages.error(request, "Error! Check your contact: victor.terron@cimat.mx describing your issue")
    
    return redirect('seeMyDiplomas')