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

from django.core.validators import MinValueValidator, MaxValueValidator

from django.db.models import Avg

from django.core.files.storage import FileSystemStorage


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

    DECISION_STATUSES = [
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
        ('minor_changes', 'Accepted with Minor Changes'),
        ('major_changes', 'Accepted with Major Changes'),
        ('accepted', 'Accepted'),
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
    decision_issued = models.CharField(max_length=20,choices=DECISION_STATUSES,default='pending')  # Status for final decision issued

    final_decision = models.CharField(
        max_length=20,
        choices=DECISION_STATUSES,
        blank=True,
        null=True
    )  

    review_round = models.PositiveIntegerField(default=1)  # Round of review


    def __str__(self):
        return self.title
    
    def get_completed_reviews_count(self):
        """Returns the number of completed reviews for this submission."""
        return self.review_set.filter(review_completed=True).count()
    
    def get_total_reviews_count(self):
        """Returns the total number of assigned reviews."""
        return self.reviewers.count()
    
    def calculate_average_score(self):
        """
        Calculates the weighted average score from all completed reviews.
        Returns:
            - None if no completed reviews
            - Float score between 0 and 10 if reviews are completed
        """
        completed_reviews = self.review_set.filter(review_completed=True)
        
        if not completed_reviews.exists():
            return None
            
        # Calculate weighted scores for each completed review
        review_scores = [review.calculate_score() for review in completed_reviews if review.calculate_score() is not None]
        
        if not review_scores:  # Si no hay scores válidos después de filtrar None
            return None
            
        # Get the average score
        average_score = sum(review_scores) / len(review_scores)
        
        return round(average_score, 2)
    
    def get_review_summary(self):
        """
        Provides a detailed summary of the review recommendations.
        """
        completed_reviews = self.review_set.filter(review_completed=True)
        total_reviews = completed_reviews.count()
        
        if not total_reviews:
            return None
            
        recommendations = {
            'must_accept': 0,
            'clear_accept': 0,
            'marginal_accept': 0,
            'marginal_reject': 0,
            'probable_reject': 0,
            'reject': 0
        }
        
        # Count recommendations
        for review in completed_reviews:
            recommendations[review.recommendation] += 1
            
        # Calculate percentages
        percentages = {
            key: (count / total_reviews) * 100 
            for key, count in recommendations.items()
        }
        
        return {
            'total_reviews': total_reviews,
            'counts': recommendations,
            'percentages': percentages
        }
    
    def get_review_status(self):
        """
        Returns the review status and completion percentage.
        """
        total_reviews = self.get_total_reviews_count()
        if total_reviews == 0:
            return "Not Assigned", 0
            
        completed_reviews = self.get_completed_reviews_count()
        completion_percentage = (completed_reviews / total_reviews) * 100
        
        if completed_reviews == 0:
            return "Pending", completion_percentage
        elif completed_reviews < total_reviews:
            return "In Progress", completion_percentage
        else:
            return "Completed", completion_percentage

    def get_final_recommendation(self):
        """
        Determines the final recommendation based on review scores and recommendations.
        Uses weighted average scores and specific thresholds for recommendations.
        """
        summary = self.get_review_summary()
        if not summary:
            return None
            
        average_score = self.calculate_average_score()
        if average_score is None:
            return None
            
        # Get percentages for accept/reject categories
        accept_percentage = (
            summary['percentages'].get('must_accept', 0) +
            summary['percentages'].get('clear_accept', 0) +
            summary['percentages'].get('marginal_accept', 0)
        )
        
        reject_percentage = (
            summary['percentages'].get('reject', 0) +
            summary['percentages'].get('probable_reject', 0) +
            summary['percentages'].get('marginal_reject', 0)
        )
        
        # Decision logic with specific thresholds
        if average_score >= 8.5 and summary['percentages'].get('must_accept', 0) > 30:
            return "Strong Accept"
        elif average_score >= 7 and accept_percentage > 60:
            return "Accept"
        elif average_score >= 5 and accept_percentage > reject_percentage:
            return "Weak Accept"
        elif average_score < 3 or reject_percentage > 70:
            return "Strong Reject"
        elif reject_percentage > accept_percentage:
            return "Reject"
        else:
            return "Borderline"
        

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
    version_number = models.PositiveIntegerField(default=1)  # Nueva columna para controlar versiones
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
    
class Review(models.Model):
    RECOMMENDATION_CHOICES = [
        ('reject', 'Reject: Content inappropriate to the conference or has little merit'),
        ('probable_reject', 'Probable Reject: Basic flaws in content or presentation or very poorly written'),
        ('marginal_reject', 'Marginal Tend to Reject: Not as badly flawed; major effort necessary'),
        ('marginal_accept', 'Marginal Tend to Accept: Content has merit, but needs improvement'),
        ('clear_accept', 'Clear Accept: Content, presentation, and writing meet professional norms'),
        ('must_accept', 'Must Accept: Candidate for outstanding submission')
    ]
    
    CATEGORIZATION_CHOICES = [
        ('highly_theoretical', 'Highly theoretical'),
        ('tends_theoretical', 'Tends towards theoretical'),
        ('balanced', 'Balanced theory and practice'),
        ('tends_practical', 'Tends toward practical'),
        ('highly_practical', 'Highly practical')
    ]
    
    FAMILIARITY_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High')
    ]
    
    DIFFERENCE_CHOICES = [
        ('different', 'Totally or largely different from other submissions'),
        ('moderate', 'Moderately different from other submissions'),
        ('identical', 'Totally or largely identical to other submissions'),
        ('unsure', 'Don\'t know')
    ]

    BEST_SUBMISSION_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('unsure', 'Unsure')
    ]

    submission = models.ForeignKey('Submission', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Review Fields
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    categorization = models.CharField(max_length=20, choices=CATEGORIZATION_CHOICES)
    
    # Value Added Fields
    new_information = models.BooleanField(default=False)
    valuable_confirmation = models.BooleanField(default=False)
    clarity_to_understanding = models.BooleanField(default=False)
    new_perspective = models.BooleanField(default=False)
    not_much = models.BooleanField(default=False)
    other_value = models.TextField(blank=True)
    
    reviewer_familiarity = models.CharField(max_length=10, choices=FAMILIARITY_CHOICES)
    best_submission_candidate = models.BooleanField(default=False)
    appropriate_length = models.BooleanField(default=False)
    difference_from_previous = models.CharField(max_length=20, choices=DIFFERENCE_CHOICES)
    
    author_comments = models.TextField()
    committee_comments = models.TextField()
    email_form = models.BooleanField(default=False)
    review_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revision_round_number = models.PositiveIntegerField(default=1)  # Round of review

    def calculate_score(self):
        score = 5  # Start with the maximum score
        
        # Scoring for recommendation
        recommendation_weights = {
            'reject': -5,
            'probable_reject': -3,
            'marginal_reject': -2,
            'marginal_accept': 1,
            'clear_accept': 3,
            'must_accept': 5,
        }
        score += recommendation_weights.get(self.recommendation, 0)

        # Scoring for categorization (example: balanced is the most favorable)
        categorization_weights = {
            'highly_theoretical': 1,
            'tends_theoretical': 2,
            'balanced': 3,
            'tends_practical': 2,
            'highly_practical': 1,
        }
        score += categorization_weights.get(self.categorization, 0)

        # Scoring for value-added fields
        if self.new_information:
            score += 1
        if self.valuable_confirmation:
            score += 1
        if self.clarity_to_understanding:
            score += 1
        if self.new_perspective:
            score += 1
        if self.not_much:
            score -= 1

        # Familiarity scoring
        familiarity_weights = {
            'low': -1,
            'moderate': 1,
            'high': 2,
        }
        score += familiarity_weights.get(self.reviewer_familiarity, 0)

        # Best submission scoring
        best_submission_weights = {
            'yes': 2,
            'no': -2,
            'unsure': 0,
        }
        score += best_submission_weights.get(self.best_submission_candidate, 0)

        # Appropriate length
        if self.appropriate_length is not None:
            score += 1 if self.appropriate_length else -1

        # Difference from previous submissions
        difference_weights = {
            'different': 2,
            'moderate': 1,
            'identical': -2,
            'unsure': 0,
        }
        score += difference_weights.get(self.difference_from_previous, 0)

        # Ensure the score is within a reasonable range
        score = max(0, min(score, 10))  # Adjust the range as needed
        return score

    def __str__(self):
        return f"Review for {self.submission.title} by {self.reviewer.username} (Score: {self.calculate_score()})"
    


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        # Si el archivo existe, lo elimina antes de guardar el nuevo
        self.delete(name)
        return name

class systemSettings(models.Model):
    allowSubmissions = models.BooleanField(default=False)
    allowScientificComitteeDiplomas = models.BooleanField(default=False)
    signature_name = models.CharField(max_length=255, blank=True, null=True)
    logoImageDecisionLetter = models.ImageField(
        upload_to='images/', 
        null=True, 
        blank=True, 
        storage=OverwriteStorage()
    )
    signatureImageDecisionLetter = models.ImageField(
        upload_to='images/', 
        null=True, 
        blank=True, 
        storage=OverwriteStorage()
    )
    availabilityDateScientificComitteeDiplomas = models.DateField(null=True, blank=True)
    scientificCommiteeDiplomasTemplate = models.FileField(upload_to='diplomasTemplates/',null=True,blank=True)  # Directory where the file will be uploaded



class News(models.Model):
    date=models.DateField()
    title=models.CharField(max_length=255)
    type=models.CharField(max_length=50,
        choices=[('info', 'Info'), ('success', 'Success'), ('danger', 'Danger')],
        default='info')
    url = models.URLField(blank=True, null=True)
    def __str__(self):
        return f"{self.fecha} - {self.titulo}"