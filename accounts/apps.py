from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        This ensures that all signals are connected properly.
        """
        import accounts.signals
