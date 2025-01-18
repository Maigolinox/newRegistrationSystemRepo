from .views import get_user_context_data

def user_context(request):
    if request.user.is_authenticated:
        return get_user_context_data(request)
    return {}