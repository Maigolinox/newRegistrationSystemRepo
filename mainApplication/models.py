import random
import string
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.conf import settings
from django.forms import ValidationError
from django_countries.fields import CountryField
from django.contrib.auth.models import AbstractUser
from django.db import models




class CustomUser(AbstractUser):
    isReviewer = models.BooleanField(default=False)
    
    def __str__(self):
        return self.email



#####################

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

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    description = models.TextField(blank=True,max_length=5000)
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
    requisites=models.CharField(default=" ",max_length=1000,null=True, blank=True,verbose_name="Requisites: ")
    allEvent=models.BooleanField(default=False,verbose_name="This event last all the congress? ")
    fileDiplomas = models.FileField(upload_to='diplomasTemplates/',null=True,blank=True)  # Directory where the file will be uploaded
    def is_ready_for_certificate(self):
        # Combina la fecha y hora de finalización
        event_end_datetime = datetime.combine(self.date, self.end_time)
        # Calcula la hora que debe pasar después del evento
        ready_time = event_end_datetime + timedelta(hours=1)
        # Verifica si la hora actual es mayor o igual que la hora lista para la constancia
        return datetime.now() >= ready_time



    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()}) - {self.ponent_name} - {self.affiliation}"

    
    
class Registration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    assisted=models.BooleanField(default=False)
    counter=models.IntegerField(default=0)
    receivedDiploma=models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'event')  # Ensure a user can register for an event only once

class CongressDate(models.Model):
    date = models.DateField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.date.strftime('%d %b %Y')

    class Meta:
        ordering = ['date']

class adminPermissions(models.Model):#for welcome kit
    kitBienvenida = models.BooleanField(default=False)#si hay o no
    kitBienvenidaAll = models.BooleanField(default=False)#si hay ¿se dara a todos?
    kitBienvenidaOnlyPayment = models.BooleanField(default=False)#sino se da a todos ¿solo a pagados?
    kitBienvenidaSchoolarships = models.BooleanField(default=False)#sino se da a todos ¿se da a becados?


class TopicArea(models.Model):
    """
    Represents a topic area that can be configured by a superuser.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

def generate_random_submission_id():
    while True:
        submission_id = ''.join(random.choices(string.digits, k=6))  # Genera un número aleatorio de 6 dígitos
        if not submission_id.startswith('0'):  # Verifica que no empiece con '0'
            return submission_id


class Submission(models.Model):
    """
    Represents a submission made by a user.
    """
    PUBLICATION_TYPES = [
        ('IEEE', 'IEEE'),
        ('Springer', 'Springer'),
        ('Other', 'Other'),
    ]
    submission_id = models.CharField(max_length=6, unique=True, default=generate_random_submission_id)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    title = models.CharField(max_length=255)
    publication_type = models.CharField(max_length=50, choices=PUBLICATION_TYPES)
    topic_areas = models.ManyToManyField(TopicArea, related_name='submissions')
    keywords = models.TextField(help_text="Comma-separated keywords.")
    abstract = models.TextField()
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_for_review = models.BooleanField(default=False)
    reviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_submissions',
        blank=True
    )  # Many-to-many relationship with reviewers
    is_withdrawn=models.BooleanField(default=False)
    assigned_reviewers=models.BooleanField(default=False)
    under_review = models.BooleanField(default=False)  # Status for being under review
    decision_issued = models.BooleanField(default=False)  # Status for final decision issued


    def __str__(self):
        return self.title
    
    def has_reviewers(self):
        """Check if there are assigned reviewers."""
        return self.reviewers.exists()

    def is_under_review(self):
        """Determine if the submission is under review."""
        return self.under_review

    def decision_issued(self):
        """Determine if a final decision has been issued."""
        return self.decision_issued

class Author(models.Model):
    """
    Represents an author associated with a submission.
    """
    HONORIFICS = [
        ('Mr.', 'Mr.'),
        ('Ms.', 'Ms.'),
        ('Dr.', 'Dr.'),
        ('Prof.', 'Prof.'),
    ]

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='authors')
    honorific = models.CharField(max_length=10, choices=HONORIFICS, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position_title = models.CharField(max_length=150, blank=True, null=True)
    organization = models.CharField(max_length=200)
    department = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postcode_zip = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.organization})"
    
class SubmissionFile(models.Model):
    """
    Represents a file uploaded by the user for a submission.
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    # description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.submission.title}"
    
class reviewersCodes(models.Model):

    code = models.CharField(max_length=255, unique=True)  # Ensures uniqueness
    used = models.BooleanField(default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewer_codes')  # Link to CustomUser
    email = models.EmailField(blank=True,null=True)  # Email to which the code was sent

    def __str__(self):
        return f"{self.code} - {'Used' if self.used else 'Unused'}"