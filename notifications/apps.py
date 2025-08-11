"""
Configuración de la aplicación de notificaciones
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Sistema de Notificaciones'
    
    def ready(self):
        """Se ejecuta cuando la aplicación está lista"""
        try:
            import notifications.signals  # noqa
        except ImportError:
            pass 