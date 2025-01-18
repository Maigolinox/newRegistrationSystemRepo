from django import forms
from .models import UserProfile, PaymentProof, Place, Event,CongressDate
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

# forms.py
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser,TopicArea,Submission,Author,SubmissionFile
from django.forms.widgets import RadioSelect
from django.utils.safestring import mark_safe

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('isReviewer',)

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields

class UserProfileForm(forms.ModelForm):
    country = CountryField().formfield(widget=CountrySelectWidget(attrs={'class': 'country-select form-select'}))

    class Meta:
        model = UserProfile
        fields = ['gender', 'country', 'state', 'university_name', 'university_address', 'user_type','FullName']
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'university_name': forms.TextInput(attrs={'class': 'form-control'}),
            'university_address': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'FullName': forms.TextInput(attrs={'class': 'form-control'}),
            # 'manualPayment': forms.TextInput(attrs={'class': 'form-control'}),
            # 'amount': forms.TextInput(attrs={'class': 'form-control'}),
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
        fields = ['title', 'description', 'date', 'start_time', 'end_time', 'place', 'event_type', 'ponent_name', 'affiliation', 'moderator', 'banner','links','requisites','allEvent','fileDiplomas']
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
            'requisites': forms.Textarea(attrs={'class': 'form-control'}),
            'links': forms.TextInput(attrs={'class': 'form-control'}),
            'banner': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'allEvent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fileDiplomas': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }

    banner = forms.ImageField(required=False)

class CongressDateForm(forms.ModelForm):
    class Meta:
        model = CongressDate
        fields = ['date', 'is_active']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class TopicAreaForm(forms.ModelForm):
    class Meta:
        model = TopicArea
        fields = ['name','description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción'}),
        }


#APARTADO PARA GENERAR LOS ENVIOS DE LOS ARTICULOS:

#PARA LOGOS SPRINGER E IEEE
class LogoRadioSelect(RadioSelect):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # Agrega la ruta de los logos según el valor
        if value == 'IEEE':
            logo_url = '/mainAppplication/static/images/IEEE.png'  # Ajusta la ruta según tu estructura
        elif value == 'Springer':
            logo_url = '/mainAppplication/static/images/SPRINGER.png'  # Ajusta la ruta según tu estructura
        else:
            logo_url = '/mainAppplication/static/images/other.png'
        
        option['label'] = mark_safe(f'<img src="{logo_url}" alt="{label}" class="publisher-logo"> {label}')
        return option

class SubmissionForm(forms.ModelForm):
    publication_type = forms.ChoiceField(
        choices=Submission.PUBLICATION_TYPES,
        widget=LogoRadioSelect(attrs={'class': 'publication-type-radio'}),
        initial=Submission.PUBLICATION_TYPES[0][0]  # Esto hará que IEEE esté seleccionado por defecto
    )
    class Meta:
        model = Submission
        fields = ['title', 'publication_type', 'topic_areas', 'keywords', 'abstract', 'comments']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter title of your submission'
            }),
            'publication_type': forms.RadioSelect(attrs={
                'class': 'publication-type-radio'
            }),
            'topic_areas': forms.CheckboxSelectMultiple(attrs={
                'class': 'topic-areas-checkbox'
            }),
            'keywords': forms.Textarea(attrs={
                'class': 'form-control auto-expand',
                'rows': 2,
                'placeholder': 'Enter keywords separated by commas'
            }),
            'abstract': forms.Textarea(attrs={
                'class': 'form-control auto-expand',
                'rows': 4,
                'placeholder': 'Enter your abstract'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control auto-expand',
                'rows': 3,
                'placeholder': 'Any additional comments?'
            })
        }

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['honorific', 'first_name', 'last_name', 'position_title', 
                 'organization', 'department', 'address', 'city', 
                 'state_province', 'postcode_zip', 'email']
        widgets = {
            'honorific': forms.Select(attrs={'class': 'form-control short'}),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control medium',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control medium',
                'placeholder': 'Enter last name'
            }),
            'position_title': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'postcode_zip': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def get_context(self, name, value, attrs):
        if attrs is None:
            attrs = {}
        attrs.setdefault('id','id_files')
        attrs.setdefault('class','custom-file-input')
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['multiple'] = True
        return context

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={
            "accept": ".jpg,.jpeg,.png,.pdf,.doc,.docx,.zip"
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'zip']
        single_file_clean = super().clean
        errors= []
        result= []
        if not data:
            return []

        # if isinstance(data, (list, tuple)):
        #     result = [single_file_clean(d, initial) for d in data]
        # else:
        #     result = [single_file_clean(data, initial)]
        # return result
        if isinstance(data, (list, tuple)):
            for d in data:
                try:
                    single_file_clean(d, initial)
                    if d.name.split('.')[-1].lower() not in allowed_extensions:
                        raise forms.ValidationError(f"{d.name} has an invalid file type.")
                    result.append(d)
                except forms.ValidationError as e:
                    errors.append(str(e))
        else:
            if data.name.split('.')[-1].lower() not in allowed_extensions:
                raise forms.ValidationError(f"{data.name} has an invalid file type.")
            result.append(data)

        if errors:
            raise forms.ValidationError(errors)

        return result

class SubmissionFileForm(forms.Form):
    files = MultipleFileField(required=False)
    def __init__(self, *args, submission=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission = submission
    # files = MultipleFileField(widget=MultipleFileInput(), required=False)
