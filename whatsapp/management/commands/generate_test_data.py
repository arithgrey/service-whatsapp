"""
Comando de Django para generar datos de prueba para el servicio de WhatsApp
Siguiendo las reglas del backend: usar Faker, sin mocks, datos reales
Ejecutar con: python manage.py generate_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from whatsapp.models import WhatsAppTemplate, WhatsAppMessage
from faker import Faker
import random
from datetime import timedelta
from django.utils import timezone

fake = Faker(['es_MX'])


class Command(BaseCommand):
    help = 'Genera datos de prueba para el servicio de WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Número de usuarios a crear'
        )
        parser.add_argument(
            '--messages',
            type=int,
            default=50,
            help='Número de mensajes a crear'
        )
        parser.add_argument(
            '--templates',
            action='store_true',
            help='Crear plantillas de prueba adicionales'
        )

    def handle(self, *args, **options):
        self.stdout.write('Generando datos de prueba para WhatsApp...')
        
        # Crear usuarios de prueba
        users = self.create_test_users(options['users'])
        
        # Crear plantillas de prueba si se solicita
        if options['templates']:
            templates = self.create_test_templates()
        else:
            templates = WhatsAppTemplate.objects.all()
        
        # Crear mensajes de prueba
        self.create_test_messages(options['messages'], users, templates)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Datos de prueba generados: {len(users)} usuarios, {options["messages"]} mensajes'
            )
        )

    def create_test_users(self, count):
        """Crea usuarios de prueba"""
        users = []
        for i in range(count):
            username = fake.user_name()
            email = fake.email()
            
            # Verificar si el usuario ya existe
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpass123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                users.append(user)
                self.stdout.write(f'✅ Usuario creado: {user.username}')
            else:
                # Usar usuario existente
                user = User.objects.get(username=username)
                users.append(user)
        
        return users

    def create_test_templates(self):
        """Crea plantillas de prueba adicionales"""
        templates_data = [
            {
                'name': 'test_custom_1',
                'category': 'custom',
                'language': 'es',
                'content': 'Mensaje de prueba personalizado para {{customer_name}}',
                'variables': ['customer_name']
            },
            {
                'name': 'test_custom_2',
                'category': 'custom',
                'language': 'en',
                'content': 'Test custom message for {{customer_name}}',
                'variables': ['customer_name']
            }
        ]
        
        templates = []
        for template_data in templates_data:
            template, created = WhatsAppTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            templates.append(template)
            
            if created:
                self.stdout.write(f'✅ Plantilla de prueba creada: {template.name}')
        
        return templates

    def create_test_messages(self, count, users, templates):
        """Crea mensajes de prueba"""
        phone_numbers = [
            '+525512345678', '+525512345679', '+525512345680',
            '+525512345681', '+525512345682', '+525512345683'
        ]
        
        message_types = ['text', 'template']
        statuses = ['pending', 'sent', 'delivered', 'read', 'failed']
        
        for i in range(count):
            # Seleccionar datos aleatorios
            user = random.choice(users)
            phone_number = random.choice(phone_numbers)
            message_type = random.choice(message_types)
            status = random.choice(statuses)
            
            # Crear contenido del mensaje
            if message_type == 'text':
                message_content = fake.text(max_nb_chars=200)
                template = None
            else:
                template = random.choice(templates) if templates else None
                message_content = template.content if template else fake.text(max_nb_chars=200)
            
            # Crear metadatos de pedido
            order_data = {
                'id': f'ORD-{fake.random_number(digits=6)}',
                'order_number': f'ORD-{fake.random_number(digits=6)}',
                'total_amount': f'{fake.random_number(digits=3)}.{fake.random_number(digits=2)}',
                'status': random.choice(['confirmed', 'processing', 'shipped', 'delivered']),
                'products': [{'name': fake.word()} for _ in range(random.randint(1, 3))]
            }
            
            # Crear el mensaje
            message = WhatsAppMessage.objects.create(
                phone_number=phone_number,
                message_type=message_type,
                message_content=message_content,
                template=template,
                status=status,
                user=user,
                order_id=order_data['id'],
                metadata=order_data
            )
            
            # Establecer timestamps según el estado
            if status in ['sent', 'delivered', 'read']:
                message.sent_at = timezone.now() - timedelta(hours=random.randint(1, 24))
                message.save(update_fields=['sent_at'])
            
            if status in ['delivered', 'read']:
                message.delivered_at = message.sent_at + timedelta(minutes=random.randint(5, 60))
                message.save(update_fields=['delivered_at'])
            
            if status == 'read':
                message.read_at = message.delivered_at + timedelta(minutes=random.randint(1, 30))
                message.save(update_fields=['read_at'])
            
            if i % 10 == 0:
                self.stdout.write(f'✅ Mensaje {i+1}/{count} creado')
        
        self.stdout.write(f'✅ {count} mensajes de prueba creados') 