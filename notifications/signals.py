"""
Señales para la aplicación de notificaciones
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Notification, NotificationTemplate, NotificationSettings


@receiver(post_save, sender=User)
def create_user_notification_settings(sender, instance, created, **kwargs):
    """Crea configuración de notificaciones por defecto para nuevos usuarios"""
    if created:
        NotificationSettings.objects.create(user=instance)


@receiver(post_save, sender=Notification)
def log_notification_status_change(sender, instance, **kwargs):
    """Registra cambios en el estado de las notificaciones"""
    if kwargs.get('update_fields') and 'status' in kwargs['update_fields']:
        # Aquí se podría agregar logging adicional o notificaciones de sistema
        pass


@receiver(post_delete, sender=NotificationTemplate)
def handle_template_deletion(sender, instance, **kwargs):
    """Maneja la eliminación de plantillas de notificación"""
    # Aquí se podría agregar lógica para notificar a los administradores
    # o para migrar notificaciones que usen esta plantilla
    pass 