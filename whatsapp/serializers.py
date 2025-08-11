"""
Serializers para el servicio de notificaciones WhatsApp
Siguiendo las reglas del backend: usar serializers en lugar de repositories
"""

from rest_framework import serializers
from .models import WhatsAppMessage, WhatsAppTemplate


class WhatsAppTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de WhatsApp"""
    
    variables_list = serializers.CharField(source='get_variables_list', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    
    class Meta:
        model = WhatsAppTemplate
        fields = [
            'id', 'name', 'category', 'category_display', 'language', 'language_display',
            'content', 'variables', 'variables_list', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        """Valida que el contenido tenga el formato correcto"""
        if not value.strip():
            raise serializers.ValidationError("El contenido no puede estar vacío")
        
        # Validar que las variables en el contenido coincidan con las definidas
        import re
        content_variables = set(re.findall(r'\{\{(\w+)\}\}', value))
        
        if hasattr(self, 'instance') and self.instance:
            # Actualización: validar contra variables existentes
            defined_variables = set(self.instance.variables)
            if content_variables and not defined_variables:
                raise serializers.ValidationError(
                    "Debe definir las variables antes de usarlas en el contenido"
                )
            undefined_variables = content_variables - defined_variables
            if undefined_variables:
                raise serializers.ValidationError(
                    f"Variables no definidas: {', '.join(undefined_variables)}"
                )
        
        return value
    
    def validate_variables(self, value):
        """Valida que las variables sean una lista válida"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Las variables deben ser una lista")
        
        # Validar que cada variable sea un string válido
        for var in value:
            if not isinstance(var, str) or not var.strip():
                raise serializers.ValidationError("Cada variable debe ser un string válido")
            if not var.replace('_', '').isalnum():
                raise serializers.ValidationError(
                    f"La variable '{var}' solo puede contener letras, números y guiones bajos"
                )
        
        return value


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes de WhatsApp"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'phone_number', 'message_type', 'message_type_display', 'message_content',
            'template', 'template_name', 'status', 'status_display', 'whatsapp_message_id',
            'error_message', 'user', 'user_email', 'order_id', 'metadata', 'created_at',
            'updated_at', 'sent_at', 'delivered_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'status', 'whatsapp_message_id', 'error_message', 'created_at',
            'updated_at', 'sent_at', 'delivered_at', 'read_at'
        ]
    
    def validate_phone_number(self, value):
        """Valida el formato del número de teléfono"""
        import re
        phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
        
        if not phone_pattern.match(value):
            raise serializers.ValidationError(
                "El número de teléfono debe estar en formato internacional válido"
            )
        
        # Normalizar el formato
        if not value.startswith('+'):
            if value.startswith('1') and len(value) == 11:
                value = '+' + value
            elif len(value) == 10:
                value = '+52' + value  # México por defecto
            else:
                value = '+' + value
        
        return value
    
    def validate_message_content(self, value):
        """Valida el contenido del mensaje"""
        if not value.strip():
            raise serializers.ValidationError("El contenido del mensaje no puede estar vacío")
        
        if len(value) > 1000:
            raise serializers.ValidationError("El mensaje no puede exceder 1000 caracteres")
        
        return value
    
    def validate(self, data):
        """Validación a nivel de objeto"""
        # Si es un mensaje de plantilla, validar que la plantilla esté activa
        if data.get('message_type') == 'template' and data.get('template'):
            template = data['template']
            if not template.is_active:
                raise serializers.ValidationError(
                    "No se puede usar una plantilla inactiva"
                )
        
        # Validar que el usuario tenga permisos para enviar mensajes
        user = data.get('user')
        if user and not user.is_active:
            raise serializers.ValidationError(
                "No se pueden enviar mensajes desde cuentas inactivas"
            )
        
        return data


class WhatsAppMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear mensajes de WhatsApp"""
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'phone_number', 'message_type', 'message_content', 'template',
            'user', 'order_id', 'metadata'
        ]
    
    def create(self, validated_data):
        """Crea un nuevo mensaje de WhatsApp"""
        # Establecer el estado inicial
        validated_data['status'] = 'pending'
        
        # Crear el mensaje
        message = WhatsAppMessage.objects.create(**validated_data)
        
        # Log de creación
        import logging
        logger = logging.getLogger('whatsapp')
        logger.info(f"Mensaje creado: {message.id} para {message.phone_number}")
        
        return message


class WhatsAppMessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar mensajes de WhatsApp"""
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'status', 'whatsapp_message_id', 'error_message', 'metadata'
        ]
    
    def update(self, instance, validated_data):
        """Actualiza el mensaje de WhatsApp"""
        # Actualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar timestamps según el estado
        from django.utils import timezone
        now = timezone.now()
        
        if validated_data.get('status') == 'sent' and not instance.sent_at:
            instance.sent_at = now
        
        if validated_data.get('status') == 'delivered' and not instance.delivered_at:
            instance.delivered_at = now
        
        if validated_data.get('status') == 'read' and not instance.read_at:
            instance.read_at = now
        
        instance.save()
        
        # Log de actualización
        import logging
        logger = logging.getLogger('whatsapp')
        logger.info(f"Mensaje actualizado: {instance.id} - Estado: {instance.status}")
        
        return instance


class WhatsAppWebhookSerializer(serializers.Serializer):
    """Serializer para webhooks de WhatsApp"""
    
    object = serializers.CharField()
    entry = serializers.ListField()
    
    def validate_object(self, value):
        """Valida que el objeto sea 'whatsapp_business_account'"""
        if value != 'whatsapp_business_account':
            raise serializers.ValidationError("Objeto webhook inválido")
        return value
    
    def validate_entry(self, value):
        """Valida la estructura de las entradas del webhook"""
        if not value:
            raise serializers.ValidationError("La entrada del webhook no puede estar vacía")
        
        for entry in value:
            if not isinstance(entry, dict):
                raise serializers.ValidationError("Cada entrada debe ser un diccionario")
            
            required_fields = ['id', 'changes']
            for field in required_fields:
                if field not in entry:
                    raise serializers.ValidationError(f"Campo requerido faltante: {field}")
        
        return value 