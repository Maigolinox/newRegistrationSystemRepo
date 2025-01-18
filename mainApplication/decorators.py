from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def superuser_required(view_func):
    """
    Decorador para restringir acceso solo a superusuarios.
    """
    def check_superuser(user):
        if not user.is_superuser:
            raise PermissionDenied  # Lanza un error 403 si no es superusuario
        return True

    return user_passes_test(check_superuser)(view_func)
