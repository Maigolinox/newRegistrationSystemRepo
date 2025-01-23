from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_migrate
from .models import systemSettings

@receiver(user_signed_up)
def populate_profile(sociallogin, user, **kwargs):
    if sociallogin.account.provider == 'google':
        user_data = user.socialaccount_set.filter(provider='google')[0].extra_data
        user.email = user_data['email']
        user.save()


@receiver(post_migrate)
def create_system_settings(sender, **kwargs):
    if sender.name == 'tu_app':  # Reemplaza 'tu_app' con el nombre de tu aplicación
        if not systemSettings.objects.exists():
            systemSettings.objects.create(
                allowSubmissions=False,
                allowScientificComitteeDiplomas=False
            )