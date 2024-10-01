from django.apps import AppConfig


class MainapplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainApplication'
    def ready(self):
        import mainApplication.signals  # Importa las señales
