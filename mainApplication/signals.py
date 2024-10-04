from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount

@receiver(user_signed_up)
def populate_profile(sociallogin, user, **kwargs):
    if sociallogin.account.provider == 'google':
        user_data = user.socialaccount_set.filter(provider='google')[0].extra_data
        user.email = user_data['email']
        user.save()