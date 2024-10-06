import base64
from datetime import timedelta, datetime
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


import pycountry
from io import BytesIO
from collections import defaultdict



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
    if registration.recibioKIT:
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
    saved = False  # Agregamos esta variable para el contexto
    
    if request.method == "POST":
        user_ids = request.POST.getlist('user_ids')
        UserProfile.objects.update(recibioKIT=False)
        for user_id in user_ids:
            user_profile = UserProfile.objects.get(id=user_id)
            user_profile.recibioKIT = True
            user_profile.save()
        saved = True  # Cambiamos a True cuando guardamos
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
    user_profiles = UserProfile.objects.select_related('user').prefetch_related('paymentproof_set').all()  # Usa prefetch_related para optimizar la consulta

    if request.method == 'POST':
        for user_profile in user_profiles:
            payment_completed = request.POST.get(f'payment_completed_{user_profile.user.id}') == 'on'
            user_profile.payment_completed = payment_completed
            user_profile.save()
        return redirect('validatePaymentAdmin')  # Ajusta esto a tu URL real

    context = {
        'user_profiles': user_profiles,
    }
    return render(request, 'validatePayment.html', context)
