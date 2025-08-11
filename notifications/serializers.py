"""
Serializers para la aplicación de notificaciones
"""

from rest_framework import serializers
from .models import NotificationTemplate, Notification, NotificationSettings


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de notificación"""
    
    variables = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'title', 'content', 
            'is_active', 'variables', 'created_at', 'updated_at', 
            'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_username']
    
    def get_variables(self, obj):
        """Extrae las variables de la plantilla"""
        return obj.get_variables()
    
    def validate_content(self, value):
        """Valida que el contenido tenga al menos una variable"""
        if '{{' not in value or '}}' not in value:
            raise serializers.ValidationError(
                "El contenido debe contener al menos una variable en formato {{variable}}"
            )
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'channel', 'channel_display', 'notification_type',
            'title', 'content', 'template', 'template_name', 'status', 'status_display',
            'scheduled_at', 'sent_at', 'delivered_at', 'error_message', 'metadata',
            'created_at', 'updated_at', 'created_by_username'
        ]
        read_only_fields = [
            'id', 'sent_at', 'delivered_at', 'created_at', 'updated_at',
            'created_by_username', 'status_display', 'channel_display'
        ]
    
    def validate_scheduled_at(self, value):
        """Valida que la fecha programada sea futura"""
        from django.utils import timezone
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha programada debe ser futura"
            )
        return value


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer para configuraciones de notificaciones"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'username', 'email', 'whatsapp_enabled', 'email_enabled',
            'sms_enabled', 'push_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'timezone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at', 'updated_at']
    
    def validate_quiet_hours(self, data):
        """Valida que las horas silenciosas sean coherentes"""
        start = data.get('quiet_hours_start')
        end = data.get('quiet_hours_end')
        
        if start and end and start == end:
            raise serializers.ValidationError(
                "Las horas de inicio y fin no pueden ser iguales"
            )
        
        return data


class SendNotificationSerializer(serializers.Serializer):
    """Serializer para envío de notificaciones"""
    
    type = serializers.ChoiceField(
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push Notification')
        ],
        help_text="Tipo de notificación a enviar"
    )
    
    recipient = serializers.DictField(
        help_text="Datos del destinatario según el tipo de notificación"
    )
    
    content = serializers.CharField(
        max_length=2000,
        help_text="Contenido de la notificación"
    )
    
    template_id = serializers.IntegerField(
        required=False,
        help_text="ID de la plantilla a usar (opcional)"
    )
    
    metadata = serializers.DictField(
        required=False,
        default=dict,
        help_text="Metadatos adicionales"
    )
    
    scheduled_at = serializers.DateTimeField(
        required=False,
        help_text="Fecha y hora para envío programado (opcional)"
    )
    
    def validate_recipient(self, value):
        """Valida los datos del destinatario según el tipo"""
        notification_type = self.initial_data.get('type')
        
        if notification_type == 'whatsapp':
            if 'phone_number' not in value:
                raise serializers.ValidationError(
                    "Para WhatsApp se requiere 'phone_number' en recipient"
                )
        elif notification_type == 'email':
            if 'email' not in value:
                raise serializers.ValidationError(
                    "Para Email se requiere 'email' en recipient"
                )
        elif notification_type == 'sms':
            if 'phone_number' not in value:
                raise serializers.ValidationError(
                    "Para SMS se requiere 'phone_number' en recipient"
                )
        
        return value


class SendBatchNotificationSerializer(serializers.Serializer):
    """Serializer para envío de notificaciones en lote"""
    
    notifications = serializers.ListField(
        child=SendNotificationSerializer(),
        min_length=1,
        max_length=100,
        help_text="Lista de notificaciones a enviar (máximo 100)"
    )
    
    def validate_notifications(self, value):
        """Valida que no haya duplicados en el lote"""
        recipients = []
        for notification in value:
            recipient_key = self._get_recipient_key(notification)
            if recipient_key in recipients:
                raise serializers.ValidationError(
                    f"Destinatario duplicado: {recipient_key}"
                )
            recipients.append(recipient_key)
        return value
    
    def _get_recipient_key(self, notification):
        """Obtiene una clave única para el destinatario"""
        recipient = notification.get('recipient', {})
        notification_type = notification.get('type', '')
        
        if notification_type == 'whatsapp':
            return f"whatsapp:{recipient.get('phone_number', '')}"
        elif notification_type == 'email':
            return f"email:{recipient.get('email', '')}"
        elif notification_type == 'sms':
            return f"sms:{recipient.get('phone_number', '')}"
        else:
            return f"{notification_type}:{str(recipient)}"


class ScheduleNotificationSerializer(serializers.Serializer):
    """Serializer para programar notificaciones"""
    
    template_id = serializers.IntegerField(
        help_text="ID de la plantilla a usar"
    )
    
    recipients = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        help_text="Lista de destinatarios"
    )
    
    scheduled_at = serializers.DateTimeField(
        help_text="Fecha y hora para el envío"
    )
    
    metadata = serializers.DictField(
        required=False,
        default=dict,
        help_text="Metadatos adicionales"
    )
    
    def validate_scheduled_at(self, value):
        """Valida que la fecha programada sea futura"""
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha programada debe ser futura"
            )
        return value 