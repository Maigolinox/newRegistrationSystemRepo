from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from .models import UserProfile
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect

def superuser_required(view_func):
    """
    Decorador para restringir acceso solo a superusuarios.
    """
    def check_superuser(user):
        if not user.is_superuser:
            raise PermissionDenied  # Lanza un error 403 si no es superusuario
        return True

    return user_passes_test(check_superuser)(view_func)


def completedProfileRequired(view_func):
    def _wrapped_view(request, *args, **kwargs):
        try:
            userProfile = UserProfile.objects.get(user_id=request.user.id)
            paymentCompleted = userProfile.payment_completed
            allowRegistration = userProfile.permitirRegistro
            userType = userProfile.user_type
        except ObjectDoesNotExist:
            # Si no existe el perfil
            return redirect('complete_profile')

        # Si el perfil no está completo, redirige

        # Si el perfil está completo, continúa con la vista
        return view_func(request, *args, **kwargs)

    return _wrapped_view