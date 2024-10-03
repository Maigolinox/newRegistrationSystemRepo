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
    userProfile = UserProfile.objects.get(user_id=userID)
    paymentCompleted = userProfile.payment_completed
    paymentObservations = userProfile.payment_completed
    uploadFile=PaymentProof.objects.filter(user_profile=userProfile).first()
    is_staff_user = request.user.is_staff  # This will be True or False
    is_staff_superuser = request.user.is_superuser  # This will be True or False
    if uploadFile:
        isRejected=uploadFile.rejected
    else:
        isRejected=False

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
    qr_text = f"{base_url}welcomeKit/{userID}/" # Update URL as needed
    qr_image = qrcode.make(qr_text)

        # Save the QR code to a BytesIO object
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_code_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Add the QR code image to the registration object for rendering
    qr_code = qr_code_image

    context = {
        'qr':qr_code,
        'userType': userProfile.get_user_type_display(),
        'paymentCompleted': paymentCompleted,
        'paymentObservations': paymentObservations,
        'uploadFile':uploadFile,
        'isRejected':isRejected,
        'form': form,  # Pass the form to the template
        'is_staff_user': is_staff_user,
        'is_staff_superuser':is_staff_superuser,
    }
    return render(request, 'payments.html', context=context)

from itertools import groupby
from operator import attrgetter

@login_required
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

    user_registrations = set()
    user_has_workshop = False
    if request.user.is_authenticated:
        user_registrations = set(Registration.objects.filter(user=request.user).values_list('event__title', flat=True))
        user_has_workshop = Registration.objects.filter(user=request.user, event__event_type='workshop').exists()
    
    identificadoresSiete=["event-3-131","event-4-132","event-5-133","event-6-134","event-7-129"]

    

    context = {
        'allowRegistration':allowRegistration,
        'identificadoresSiete':identificadoresSiete,
        'paymentCompleted': paymentCompleted,
        'events_by_date': events_by_date,
        'time_slots': time_slots,
        'places': places,
        'congress_dates': congress_dates,
        'user_registrations': list(user_registrations),
        'user_has_workshop': user_has_workshop,
        'is_staff_user': is_staff_user,
        'is_staff_superuser':is_staff_superuser,
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
        # Get all events with the same title
        events = Event.objects.filter(title=event_title)
        if not events.exists():
            return JsonResponse({'success': False, 'error': 'Event not found'})
        
        # Check if the event is a workshop
        is_workshop = events.first().event_type == 'workshop'
        
        # Check if user is already registered for any of these events
        if Registration.objects.filter(user=request.user, event__in=events).exists():
            return JsonResponse({'success': False, 'error': 'You are already registered for this event'})
        
        # If it's a workshop, check if user is already registered for any workshop
        if is_workshop and Registration.objects.filter(user=request.user, event__event_type='workshop').exists():
            return JsonResponse({'success': False, 'error': 'You can only register for one workshop'})
        
        # Register the user for the first event in the list
        Registration.objects.create(user=request.user, event=events.first())
        return JsonResponse({'success': True})
    except IntegrityError:
        return JsonResponse({'success': False, 'error': 'You are already registered for this event'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@staff_member_required
def register_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new event to the database
            return redirect('schedule')  # Redirect to the schedule or another page
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
    event = get_object_or_404(Event, id=event_id)  # Fetch the event object by ID

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)  # Load the form with the event instance
        if form.is_valid():
            form.save()  # Save changes to the event
            messages.success(request, 'Event updated successfully.')
            return redirect('schedule')  # Redirect to the schedule or another page
    else:
        form = EventForm(instance=event)  # Pre-fill the form with the event data
    
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
    user_profiles = UserProfile.objects.select_related('user').all()
    
    if request.method == 'POST':
        for user_profile in user_profiles:
            payment_completed = request.POST.get(f'payment_completed_{user_profile.user.id}') == 'on'
            user_profile.payment_completed = payment_completed
            user_profile.save()
        return redirect('validatePaymentAdmin')  # Adjust this to your actual URL name for this view


    context={
        'user_profiles': user_profiles,
    }
    return render(request,'validatePayment.html',context)