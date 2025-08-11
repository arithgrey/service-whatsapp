"""
Modelos para la aplicación de notificaciones
Siguiendo las reglas del backend: Django 4.2.7, sin Redis innecesario, manejo de errores robusto
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator


class NotificationTemplate(models.Model):
    """Plantilla para notificaciones"""
    
    NOTIFICATION_TYPES = [
        ('order_confirmation', 'Confirmación de Pedido'),
        ('order_status_update', 'Actualización de Estado'),
        ('order_shipped', 'Pedido Enviado'),
        ('order_delivered', 'Pedido Entregado'),
        ('order_cancelled', 'Pedido Cancelado'),
        ('payment_reminder', 'Recordatorio de Pago'),
        ('custom', 'Personalizada'),
    ]
    
    name = models.CharField(
        max_length=100, 
        verbose_name="Nombre de la plantilla",
        help_text="Nombre descriptivo de la plantilla"
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name="Tipo de notificación"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título de la notificación"
    )
    
    content = models.TextField(
        verbose_name="Contenido",
        help_text="Contenido de la notificación con variables {{variable}}",
        validators=[
            MinLengthValidator(10, "El contenido debe tener al menos 10 caracteres"),
            MaxLengthValidator(2000, "El contenido no puede exceder 2000 caracteres")
        ]
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la plantilla está disponible para uso"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por"
    )
    
    class Meta:
        verbose_name = "Plantilla de notificación"
        verbose_name_plural = "Plantillas de notificaciones"
        ordering = ['-created_at']
        unique_together = ['name', 'notification_type']
        
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"
    
    def get_variables(self):
        """Extrae las variables de la plantilla"""
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', self.content)
        return list(set(variables))


class Notification(models.Model):
    """Modelo para almacenar notificaciones enviadas"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregada'),
        ('failed', 'Fallida'),
        ('cancelled', 'Cancelada'),
    ]
    
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    recipient = models.CharField(
        max_length=100,
        verbose_name="Destinatario",
        help_text="Identificador del destinatario (teléfono, email, etc.)"
    )
    
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default='whatsapp',
        verbose_name="Canal"
    )
    
    notification_type = models.CharField(
        max_length=50,
        verbose_name="Tipo de notificación"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Título",
        blank=True
    )
    
    content = models.TextField(
        verbose_name="Contenido"
    )
    
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Plantilla utilizada"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Programada para"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Enviada el"
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Entregada el"
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name="Mensaje de error"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadatos adicionales"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por"
    )
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'channel']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['scheduled_at', 'status']),
        ]
        
    def __str__(self):
        return f"{self.notification_type} a {self.recipient} ({self.get_status_display()})"
    
    def mark_as_sent(self):
        """Marca la notificación como enviada"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_delivered(self):
        """Marca la notificación como entregada"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_failed(self, error_message=""):
        """Marca la notificación como fallida"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def cancel(self):
        """Cancela la notificación"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.save(update_fields=['status'])
    
    def is_schedulable(self):
        """Verifica si la notificación puede ser programada"""
        return self.status == 'pending' and self.scheduled_at and self.scheduled_at > timezone.now()
    
    def is_retryable(self):
        """Verifica si la notificación puede ser reintentada"""
        return self.status in ['failed', 'pending']


class NotificationSettings(models.Model):
    """Configuración de notificaciones por usuario"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    
    whatsapp_enabled = models.BooleanField(
        default=True,
        verbose_name="WhatsApp habilitado"
    )
    
    email_enabled = models.BooleanField(
        default=True,
        verbose_name="Email habilitado"
    )
    
    sms_enabled = models.BooleanField(
        default=False,
        verbose_name="SMS habilitado"
    )
    
    push_enabled = models.BooleanField(
        default=True,
        verbose_name="Push notifications habilitado"
    )
    
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Inicio de horas silenciosas"
    )
    
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Fin de horas silenciosas"
    )
    
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name="Zona horaria"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )
    
    class Meta:
        verbose_name = "Configuración de notificaciones"
        verbose_name_plural = "Configuraciones de notificaciones"
        
    def __str__(self):
        return f"Configuración de {self.user.username}"
    
    def is_quiet_hours(self, current_time=None):
        """Verifica si estamos en horas silenciosas"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
            
        if current_time is None:
            current_time = timezone.now().time()
            
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:  # Horas silenciosas cruzan la medianoche
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end 