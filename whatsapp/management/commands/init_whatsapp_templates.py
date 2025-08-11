"""
Comando de Django para inicializar plantillas básicas de WhatsApp
Ejecutar con: python manage.py init_whatsapp_templates
"""

from django.core.management.base import BaseCommand
from whatsapp.models import WhatsAppTemplate


class Command(BaseCommand):
    help = 'Inicializa las plantillas básicas de WhatsApp para notificaciones de pedidos'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando plantillas de WhatsApp...')
        
        templates_data = [
            {
                'name': 'order_confirmation',
                'category': 'order_confirmation',
                'language': 'es',
                'content': '''¡Hola {{customer_name}}! 

Tu pedido #{{order_id}} ha sido confirmado exitosamente.

📦 **Detalles del pedido:**
• Total: {{order_total}}
• Fecha: {{order_date}}
• Dirección de entrega: {{delivery_address}}

🚚 **Tiempo estimado de entrega:** {{estimated_delivery}}

Te mantendremos informado sobre el estado de tu pedido. ¡Gracias por tu compra!

Para consultas, responde a este mensaje o contacta nuestro servicio al cliente.''',
                'variables': ['customer_name', 'order_id', 'order_total', 'order_date', 'delivery_address', 'estimated_delivery']
            },
            {
                'name': 'order_status_update',
                'category': 'order_status_update',
                'language': 'es',
                'content': '''¡Hola! 

Tu pedido #{{order_id}} ha sido actualizado.

🔄 **Nuevo estado:** {{status}}
⏰ **Actualizado:** {{update_time}}

{% if additional_info %}
📝 **Información adicional:**
{{additional_info}}
{% endif %}

Te notificaremos cuando haya más actualizaciones. ¡Gracias por tu paciencia!''',
                'variables': ['order_id', 'status', 'update_time', 'additional_info']
            },
            {
                'name': 'order_delivered',
                'category': 'order_delivered',
                'language': 'es',
                'content': '''¡Excelente noticia! 🎉

Tu pedido #{{order_id}} ha sido entregado exitosamente.

✅ **Estado:** Entregado
📅 **Fecha de entrega:** {{delivery_date}}

Esperamos que estés satisfecho con tu compra. Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.

¡Gracias por elegirnos! 😊''',
                'variables': ['order_id', 'delivery_date']
            },
            {
                'name': 'order_cancelled',
                'category': 'order_cancelled',
                'language': 'es',
                'content': '''Hola,

Tu pedido #{{order_id}} ha sido cancelado.

❌ **Estado:** Cancelado
⏰ **Cancelado:** {{cancellation_time}}

{% if cancellation_reason %}
📝 **Motivo:** {{cancellation_reason}}
{% endif %}

Si tienes alguna pregunta sobre la cancelación, por favor contáctanos.

Lamentamos cualquier inconveniente causado.''',
                'variables': ['order_id', 'cancellation_time', 'cancellation_reason']
            },
            {
                'name': 'payment_confirmed',
                'category': 'payment_confirmed',
                'language': 'es',
                'content': '''¡Pago confirmado! 💳✅

Tu pago por el pedido #{{order_id}} ha sido procesado exitosamente.

💰 **Monto:** {{payment_amount}}
💳 **Método:** {{payment_method}}
⏰ **Confirmado:** {{confirmation_time}}

Tu pedido está siendo preparado y será enviado pronto.

¡Gracias por tu compra! 🎉''',
                'variables': ['order_id', 'payment_amount', 'payment_method', 'confirmation_time']
            },
            {
                'name': 'shipping_update',
                'category': 'shipping_update',
                'language': 'es',
                'content': '''🚚 **Actualización de envío**

Tu pedido #{{order_id}} está en camino.

📦 **Estado del envío:** {{shipping_status}}
📍 **Ubicación actual:** {{current_location}}
⏰ **Estimado de entrega:** {{estimated_delivery}}

{% if tracking_number %}
📋 **Número de seguimiento:** {{tracking_number}}
{% endif %}

Te notificaremos cuando llegue a tu destino.''',
                'variables': ['order_id', 'shipping_status', 'current_location', 'estimated_delivery', 'tracking_number']
            },
            {
                'name': 'welcome_message',
                'category': 'welcome_message',
                'language': 'es',
                'content': '''¡Bienvenido a Enid Store! 🎉

Hola {{customer_name}}, nos alegra que te hayas unido a nuestra comunidad.

🛍️ **Descubre nuestros productos:**
• Ofertas exclusivas
• Envío rápido y seguro
• Atención al cliente 24/7

¡Gracias por elegirnos! 😊''',
                'variables': ['customer_name']
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates_data:
            template, created = WhatsAppTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✅ Plantilla creada: {template.name}')
            else:
                # Actualizar plantilla existente
                for key, value in template_data.items():
                    if key != 'name':
                        setattr(template, key, value)
                template.save()
                updated_count += 1
                self.stdout.write(f'🔄 Plantilla actualizada: {template.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Inicialización completada: {created_count} creadas, {updated_count} actualizadas'
            )
        ) 