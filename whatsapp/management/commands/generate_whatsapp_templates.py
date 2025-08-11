"""
Comando de Django para generar plantillas iniciales de WhatsApp para pedidos
Siguiendo las reglas del backend: TDD, sin mocks, usando Faker
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from whatsapp.models import WhatsAppTemplate
from faker import Faker

fake = Faker(['es_MX'])


class Command(BaseCommand):
    help = 'Genera plantillas iniciales de WhatsApp para notificaciones de pedidos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de plantillas existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Generando plantillas de WhatsApp para pedidos...')
        )

        # Plantillas para diferentes tipos de notificaciones de pedidos
        templates_data = [
            {
                'name': 'Confirmación de Pedido',
                'category': 'order_confirmation',
                'language': 'es',
                'content': """¡Hola {{customer_name}}! 

Tu pedido #{{order_number}} ha sido confirmado exitosamente.

📦 **Detalles del pedido:**
• Número: {{order_number}}
• Fecha: {{order_date}}
• Total: ${{total_amount}}
• Productos: {{product_count}} artículo(s)

🚚 **Envío:**
{{shipping_address}}

Gracias por tu compra. Te mantendremos informado sobre el estado de tu pedido.

¿Tienes alguna pregunta? Responde a este mensaje.""",
                'variables': ['customer_name', 'order_number', 'order_date', 'total_amount', 'product_count', 'shipping_address']
            },
            {
                'name': 'Actualización de Estado',
                'category': 'order_status_update',
                'language': 'es',
                'content': """¡Hola {{customer_name}}!

Tu pedido #{{order_number}} ha sido actualizado:

🔄 **Nuevo estado:** {{order_status}}

📦 **Detalles del pedido:**
• Número: {{order_number}}
• Total: ${{total_amount}}

Te notificaremos cuando haya más actualizaciones.""",
                'variables': ['customer_name', 'order_number', 'order_status', 'total_amount']
            },
            {
                'name': 'Pedido Entregado',
                'category': 'order_delivered',
                'language': 'es',
                'content': """¡Hola {{customer_name}}!

🎉 **¡Tu pedido #{{order_number}} ha sido entregado!**

📦 **Resumen del pedido:**
• Número: {{order_number}}
• Total: ${{total_amount}}
• Productos: {{product_count}} artículo(s)

Esperamos que estés satisfecho con tu compra. 

¿Te gustó tu experiencia? ¡Déjanos una reseña!""",
                'variables': ['customer_name', 'order_number', 'total_amount', 'product_count']
            },
            {
                'name': 'Pedido Cancelado',
                'category': 'order_cancelled',
                'language': 'es',
                'content': """¡Hola {{customer_name}}!

❌ **Tu pedido #{{order_number}} ha sido cancelado.**

📦 **Detalles del pedido:**
• Número: {{order_number}}
• Total: ${{total_amount}}

Si tienes alguna pregunta sobre la cancelación, no dudes en contactarnos.

Esperamos verte pronto con una nueva compra.""",
                'variables': ['customer_name', 'order_number', 'total_amount']
            },
            {
                'name': 'Pago Confirmado',
                'category': 'payment_confirmed',
                'language': 'es',
                'content': """¡Hola {{customer_name}}!

💳 **¡Tu pago ha sido confirmado!**

📦 **Detalles del pedido:**
• Número: {{order_number}}
• Total: ${{total_amount}}
• Método de pago: {{payment_method}}

Tu pedido está siendo procesado y pronto comenzará el envío.

¡Gracias por tu compra!""",
                'variables': ['customer_name', 'order_number', 'total_amount', 'payment_method']
            },
            {
                'name': 'Actualización de Envío',
                'category': 'shipping_update',
                'language': 'es',
                'content': """¡Hola {{customer_name}}!

🚚 **Actualización de envío para tu pedido #{{order_number}}**

📦 **Estado del envío:** {{order_status}}

📍 **Dirección de entrega:**
{{shipping_address}}

Tu pedido está en camino. Te notificaremos cuando llegue.""",
                'variables': ['customer_name', 'order_number', 'order_status', 'shipping_address']
            }
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates_data:
            template, created = WhatsAppTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'category': template_data['category'],
                    'language': template_data['language'],
                    'content': template_data['content'],
                    'variables': template_data['variables'],
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Plantilla creada: {template.name}')
                )
            elif options['force']:
                # Actualizar plantilla existente si se fuerza
                template.category = template_data['category']
                template.language = template_data['language']
                template.content = template_data['content']
                template.variables = template_data['variables']
                template.is_active = True
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Plantilla actualizada: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Plantilla ya existe: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado!\n'
                f'• Plantillas creadas: {created_count}\n'
                f'• Plantillas actualizadas: {updated_count}\n'
                f'• Total de plantillas: {WhatsAppTemplate.objects.count()}'
            )
        )

        # Mostrar resumen de plantillas por categoría
        self.stdout.write('\n📋 **Resumen de plantillas por categoría:**')
        for category, _ in WhatsAppTemplate.CATEGORY_CHOICES:
            count = WhatsAppTemplate.objects.filter(category=category, is_active=True).count()
            if count > 0:
                self.stdout.write(f'• {category}: {count} plantilla(s)') 