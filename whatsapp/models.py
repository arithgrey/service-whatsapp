"""
Modelos para el servicio de notificaciones WhatsApp
Siguiendo las reglas del backend: Django 4.2.7, estructura clara, sin Redis innecesario
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class WhatsAppTemplate(models.Model):
    """
    Plantillas de mensajes de WhatsApp para diferentes tipos de notificaciones
    """
    CATEGORY_CHOICES = (
        ('order_confirmation', 'Confirmación de Pedido'),
        ('order_status_update', 'Actualización de Estado'),
        ('order_delivered', 'Pedido Entregado'),
        ('order_cancelled', 'Pedido Cancelado'),
        ('payment_confirmed', 'Pago Confirmado'),
        ('shipping_update', 'Actualización de Envío'),
        ('welcome_message', 'Mensaje de Bienvenida'),
        ('custom', 'Personalizado'),
    )
    
    LANGUAGE_CHOICES = (
        ('es', 'Español'),
        ('en', 'English'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='es')
    content = models.TextField(help_text='Contenido del mensaje con variables {{variable}}')
    variables = models.JSONField(
        default=list,
        help_text='Lista de variables disponibles en la plantilla'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Plantilla de WhatsApp'
        verbose_name_plural = 'Plantillas de WhatsApp'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()}) - {self.get_language_display()}"
    
    def get_variables_list(self):
        """Retorna la lista de variables como string legible"""
        return ', '.join(self.variables) if self.variables else 'Sin variables'


class WhatsAppMessage(models.Model):
    """
    Registro de mensajes enviados por WhatsApp
    """
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Texto'),
        ('template', 'Plantilla'),
        ('media', 'Multimedia'),
        ('interactive', 'Interactivo'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    )
    
    # Información del mensaje
    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='El número de teléfono debe estar en formato internacional'
            )
        ]
    )
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    message_content = models.TextField()
    template = models.ForeignKey(
        WhatsAppTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages'
    )
    
    # Estado y tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Metadatos
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_messages'
    )
    order_id = models.CharField(max_length=50, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje de WhatsApp'
        verbose_name_plural = 'Mensajes de WhatsApp'
        indexes = [
            models.Index(fields=['phone_number', 'status']),
            models.Index(fields=['order_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Mensaje {self.id} a {self.phone_number} - {self.get_status_display()}"
    
    def mark_as_sent(self, whatsapp_message_id):
        """Marca el mensaje como enviado"""
        from django.utils import timezone
        self.status = 'sent'
        self.whatsapp_message_id = whatsapp_message_id
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'whatsapp_message_id', 'sent_at'])
    
    def mark_as_delivered(self):
        """Marca el mensaje como entregado"""
        from django.utils import timezone
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_read(self):
        """Marca el mensaje como leído"""
        from django.utils import timezone
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_failed(self, error_message):
        """Marca el mensaje como fallido"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    @property
    def is_successful(self):
        """Retorna True si el mensaje fue enviado exitosamente"""
        return self.status in ['sent', 'delivered', 'read']
    
    @property
    def delivery_time(self):
        """Retorna el tiempo de entrega si está disponible"""
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None 