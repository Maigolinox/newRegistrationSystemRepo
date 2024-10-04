from django import forms
from .models import UserProfile, PaymentProof, Place, Event,CongressDate
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

class UserProfileForm(forms.ModelForm):
    country = CountryField().formfield(widget=CountrySelectWidget(attrs={'class': 'country-select form-select'}))

    class Meta:
        model = UserProfile
        fields = ['gender', 'country', 'state', 'university_name', 'university_address', 'user_type']
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'university_name': forms.TextInput(attrs={'class': 'form-control'}),
            'university_address': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
        }

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ['file']
        widgets={
            'file':forms.ClearableFileInput(attrs={'class':'form-control'})
        }

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['name', 'capacity']  # Adjust fields as necessary
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'start_time', 'end_time', 'place', 'event_type', 'ponent_name', 'affiliation', 'moderator', 'banner','links']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'place': forms.Select(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'ponent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control'}),
            'moderator': forms.TextInput(attrs={'class': 'form-control'}),
            'links': forms.TextInput(attrs={'class': 'form-control'}),
            'banner': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    banner = forms.ImageField(required=False)

class CongressDateForm(forms.ModelForm):
    class Meta:
        model = CongressDate
        fields = ['date', 'is_active']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }