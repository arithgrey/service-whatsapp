#!/usr/bin/env python
"""
Script para inicializar plantillas básicas de WhatsApp
Ejecutar con: python manage.py shell < initial_whatsapp_templates.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from whatsapp.models import WhatsAppTemplate

def create_basic_templates():
    """Crea las plantillas básicas para notificaciones de pedidos"""
    
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

Tu pago para el pedido #{{order_id}} ha sido procesado exitosamente.

💰 **Monto:** {{payment_amount}}
📅 **Fecha de pago:** {{payment_date}}
💳 **Método:** {{payment_method}}

Tu pedido está siendo preparado y pronto comenzará el proceso de envío.

¡Gracias por tu pago! 🚀''',
            'variables': ['order_id', 'payment_amount', 'payment_date', 'payment_method']
        },
        {
            'name': 'shipping_update',
            'category': 'shipping_update',
            'language': 'es',
            'content': '''🚚 **Actualización de envío**

Tu pedido #{{order_id}} está en camino.

📦 **Estado:** {{shipping_status}}
📍 **Ubicación actual:** {{current_location}}
⏰ **Actualizado:** {{update_time}}

{% if estimated_arrival %}
🕐 **Llegada estimada:** {{estimated_arrival}}
{% endif %}

{% if tracking_number %}
🔍 **Número de seguimiento:** {{tracking_number}}
{% endif %}

¡Tu pedido llegará pronto! 📍''',
            'variables': ['order_id', 'shipping_status', 'current_location', 'update_time', 'estimated_arrival', 'tracking_number']
        },
        {
            'name': 'welcome_message',
            'category': 'welcome_message',
            'language': 'es',
            'content': '''¡Bienvenido a Enid Store! 🎉

Hola {{customer_name}}, 

Gracias por registrarte en nuestra tienda. Estamos emocionados de tenerte como cliente.

🛍️ **¿Qué puedes hacer?**
• Explorar nuestros productos
• Realizar pedidos
• Recibir notificaciones sobre el estado de tus compras
• Contactar nuestro servicio al cliente

Si tienes alguna pregunta, no dudes en responder a este mensaje.

¡Bienvenido a la familia Enid! 😊''',
            'variables': ['customer_name']
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for template_data in templates_data:
        template, created = WhatsAppTemplate.objects.get_or_create(
            name=template_data['name'],
            language=template_data['language'],
            defaults={
                'category': template_data['category'],
                'content': template_data['content'],
                'variables': template_data['variables'],
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Plantilla creada: {template.name} ({template.get_category_display()})")
            created_count += 1
        else:
            # Actualizar si ya existe
            template.category = template_data['category']
            template.content = template_data['content']
            template.variables = template_data['variables']
            template.is_active = True
            template.save()
            print(f"🔄 Plantilla actualizada: {template.name} ({template.get_category_display()})")
            updated_count += 1
    
    print(f"\n📊 Resumen:")
    print(f"   • Plantillas creadas: {created_count}")
    print(f"   • Plantillas actualizadas: {updated_count}")
    print(f"   • Total procesadas: {len(templates_data)}")
    
    return created_count, updated_count

def create_english_templates():
    """Crea versiones en inglés de las plantillas principales"""
    
    english_templates = [
        {
            'name': 'order_confirmation_en',
            'category': 'order_confirmation',
            'language': 'en',
            'content': '''Hello {{customer_name}}! 

Your order #{{order_id}} has been successfully confirmed.

📦 **Order Details:**
• Total: {{order_total}}
• Date: {{order_date}}
• Delivery address: {{delivery_address}}

🚚 **Estimated delivery time:** {{estimated_delivery}}

We'll keep you informed about your order status. Thank you for your purchase!

For inquiries, reply to this message or contact our customer service.''',
            'variables': ['customer_name', 'order_id', 'order_total', 'order_date', 'delivery_address', 'estimated_delivery']
        },
        {
            'name': 'order_status_update_en',
            'category': 'order_status_update',
            'language': 'en',
            'content': '''Hello! 

Your order #{{order_id}} has been updated.

🔄 **New status:** {{status}}
⏰ **Updated:** {{update_time}}

{% if additional_info %}
📝 **Additional information:**
{{additional_info}}
{% endif %}

We'll notify you when there are more updates. Thank you for your patience!''',
            'variables': ['order_id', 'status', 'update_time', 'additional_info']
        }
    ]
    
    created_count = 0
    
    for template_data in english_templates:
        template, created = WhatsAppTemplate.objects.get_or_create(
            name=template_data['name'],
            language=template_data['language'],
            defaults={
                'category': template_data['category'],
                'content': template_data['content'],
                'variables': template_data['variables'],
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Plantilla en inglés creada: {template.name}")
            created_count += 1
    
    print(f"\n🌍 Plantillas en inglés creadas: {created_count}")
    return created_count

if __name__ == '__main__':
    print("🚀 Inicializando plantillas de WhatsApp...\n")
    
    # Crear plantillas básicas en español
    created, updated = create_basic_templates()
    
    # Crear plantillas en inglés
    english_created = create_english_templates()
    
    print(f"\n🎉 ¡Inicialización completada!")
    print(f"   • Total de plantillas disponibles: {WhatsAppTemplate.objects.count()}")
    print(f"   • Plantillas activas: {WhatsAppTemplate.objects.filter(is_active=True).count()}")
    
    # Mostrar resumen de plantillas
    print(f"\n📋 Plantillas disponibles:")
    for template in WhatsAppTemplate.objects.filter(is_active=True).order_by('category', 'language'):
        print(f"   • {template.name} ({template.get_category_display()}) - {template.get_language_display()}") 