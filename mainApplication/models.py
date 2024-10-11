from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.conf import settings
from django.forms import ValidationError
from django_countries.fields import CountryField

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    
    USER_TYPE_CHOICES = (
        ('author', 'Author'),
        ('public', 'General Public'),
        ('student', 'Student'),
        # ('guest', 'Guest'),
        # ('other', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    state = models.CharField(max_length=100)
    country = CountryField()
    university_name = models.CharField(max_length=255)
    university_address = models.CharField(max_length=255)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    payment_completed=models.BooleanField(default=0)
    payment_observarions=models.CharField(default=" ",max_length=255,null=True, blank=True)
    transactionID=models.CharField(default=" ",max_length=255, null=True, blank=True)
    recibioKIT=models.BooleanField(default=False)
    permitirRegistro=models.BooleanField(default=False)
    FullName=models.CharField(max_length=255, blank=True, null=True, verbose_name="Full Name (The name you write will be the one under which your certificates will be issued)")  # Nombre completo
    manualPayment=models.BooleanField(default=False)
    amount=models.CharField(default=" ",max_length=255, null=True, blank=True)


    # paper_id = models.CharField(max_length=100, blank=True, null=True)  # ID del artículo
    # paper_name = models.CharField(max_length=255, blank=True, null=True)  # Nombre del artículo

    def __str__(self):
        return self.user.username

class PaymentProof(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Link to the user
    file = models.FileField(upload_to='payment_proofs/')  # Directory where the file will be uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)
    rejected=models.BooleanField(default=False)


class Place(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=0)  # Add capacity field

    def __str__(self):
        return self.name


class Event(models.Model):
    EVENT_TYPES = [
        ('ieee', 'IEEE Article'),
        ('springer', 'Springer Article'),
        ('keynote', 'Keynote'),
        ('lunch', 'Lunch'),
        ('workshop', 'Workshop'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default="other")
    ponent_name = models.CharField(max_length=255, blank=True)
    affiliation = models.CharField(max_length=255, blank=True)
    moderator = models.CharField(max_length=255, blank=True)
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    links=models.CharField(default=" ",max_length=255,null=True, blank=True,verbose_name="Links of online meeting: ")
    requisites=models.CharField(default=" ",max_length=255,null=True, blank=True,verbose_name="Requisites: ")
    allEvent=models.BooleanField(default=False,verbose_name="This event last all the congress? ")


    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()}) - {self.ponent_name} - {self.affiliation}"

    
    
class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    assisted=models.BooleanField(default=False)
    counter=models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'event')  # Ensure a user can register for an event only once

class CongressDate(models.Model):
    date = models.DateField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.date.strftime('%d %b %Y')

    class Meta:
        ordering = ['date']
