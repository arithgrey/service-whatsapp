"""
Tests TDD para la aplicación de notificaciones
Siguiendo las reglas del backend: TDD obligatorio, sin mocks, usando Faker
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from faker import Faker
from .models import Notification, NotificationTemplate
from .serializers import NotificationSerializer, NotificationTemplateSerializer

User = get_user_model()
fake = Faker('es_MX')

class NotificationTemplateModelTest(TestCase):
    """Tests para el modelo NotificationTemplate"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.template_data = {
            'name': fake.word(),
            'notification_type': 'order_confirmation',
            'title': fake.sentence(),
            'content': fake.text(max_nb_chars=500),
            'is_active': True
        }
    
    def test_create_notification_template(self):
        """Test: Crear una plantilla de notificación"""
        template = NotificationTemplate.objects.create(**self.template_data)
        self.assertEqual(template.name, self.template_data['name'])
        self.assertEqual(template.notification_type, self.template_data['notification_type'])
        self.assertTrue(template.is_active)
    
    def test_template_str_representation(self):
        """Test: Representación string de la plantilla"""
        template = NotificationTemplate.objects.create(**self.template_data)
        expected_str = f"{template.name} ({template.get_notification_type_display()})"
        self.assertEqual(str(template), expected_str)

class NotificationModelTest(TestCase):
    """Tests para el modelo Notification"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = User.objects.create_user(
            username=fake.user_name(),
            email=fake.email(),
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name=fake.word(),
            notification_type='order_confirmation',
            title=fake.sentence(),
            content=fake.text(max_nb_chars=200),
            is_active=True
        )
        
        self.notification_data = {
            'created_by': self.user,
            'template': self.template,
            'recipient': fake.phone_number(),
            'channel': 'whatsapp',
            'notification_type': 'order_confirmation',
            'title': 'Test Notification',
            'content': 'Test content for notification',
            'status': 'pending'
        }
    
    def test_create_notification(self):
        """Test: Crear una notificación"""
        notification = Notification.objects.create(**self.notification_data)
        self.assertEqual(notification.created_by, self.user)
        self.assertEqual(notification.status, 'pending')
        self.assertEqual(notification.channel, 'whatsapp')
    
    def test_notification_str_representation(self):
        """Test: Representación string de la notificación"""
        notification = Notification.objects.create(**self.notification_data)
        expected_str = f"{notification.notification_type} a {notification.recipient} ({notification.get_status_display()})"
        self.assertEqual(str(notification), expected_str)

class NotificationSerializerTest(TestCase):
    """Tests para el serializer NotificationSerializer"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = User.objects.create_user(
            username=fake.user_name(),
            email=fake.email(),
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name=fake.word(),
            notification_type='order_confirmation',
            title=fake.sentence(),
            content=fake.text(max_nb_chars=200),
            is_active=True
        )
        
        self.notification_data = {
            'created_by': self.user.id,
            'template': self.template.id,
            'recipient': fake.phone_number(),
            'channel': 'whatsapp',
            'notification_type': 'order_confirmation',
            'title': 'Test Notification',
            'content': 'Test content for notification'
        }
    
    def test_notification_serializer_valid_data(self):
        """Test: Serializer con datos válidos"""
        serializer = NotificationSerializer(data=self.notification_data)
        self.assertTrue(serializer.is_valid())
    
    def test_notification_serializer_invalid_data(self):
        """Test: Serializer con datos inválidos"""
        invalid_data = self.notification_data.copy()
        invalid_data['channel'] = 'INVALID_CHANNEL'  # Canal inválido
        serializer = NotificationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('channel', serializer.errors)

class NotificationAPITest(APITestCase):
    """Tests de API para notificaciones"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.template = NotificationTemplate.objects.create(
            name='test_template',
            notification_type='order_confirmation',
            title='Test Subject',
            content='Hello {{user_name}}, your order {{order_id}} is ready',
            is_active=True
        )
        
        self.notification_data = {
            'type': 'whatsapp',
            'recipient': {'phone_number': fake.phone_number()},
            'content': 'Test content for notification'
        }
    
    def test_send_notification_api(self):
        """Test: Enviar notificación via API"""
        url = reverse('notifications:send_notification')
        response = self.client.post(url, self.notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 1)
    
    def test_batch_notifications_api(self):
        """Test: Enviar notificaciones en lote via API"""
        batch_data = {
            'notifications': [
                self.notification_data,
                {
                    'type': 'whatsapp',
                    'recipient': {'phone_number': fake.phone_number()},
                    'content': 'Test content for notification 2'
                }
            ]
        }
        
        url = reverse('notifications:send_batch_notification')
        response = self.client.post(url, batch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 2)
    
    def test_notification_list_api(self):
        """Test: Listar notificaciones via API"""
        # Crear notificación primero
        notification = Notification.objects.create(
            created_by=self.user,
            template=self.template,
            recipient=fake.phone_number(),
            channel='whatsapp',
            notification_type='order_confirmation',
            title='Test Notification',
            content='Test content for notification',
            status='pending'
        )
        
        url = reverse('notifications:notification_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('/api/whatsapp/messages/', response.data['message'])
    
    def test_notification_settings_api(self):
        """Test: Obtener configuración de notificaciones via API"""
        url = reverse('notifications:notification_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('whatsapp_enabled', response.data['settings'])
        self.assertIn('supported_types', response.data['settings'])

class NotificationIntegrationTest(APITestCase):
    """Tests de integración para notificaciones"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear plantilla
        self.template = NotificationTemplate.objects.create(
            name='order_status_update',
            notification_type='order_status_update',
            title='Actualización de pedido',
            content='Tu pedido {{order_id}} tiene estado: {{status}}',
            is_active=True
        )
    
    def test_complete_notification_flow(self):
        """Test: Flujo completo de notificación"""
        # 1. Enviar notificación
        notification_data = {
            'type': 'whatsapp',
            'recipient': {'phone_number': fake.phone_number()},
            'content': 'Tu pedido ORD-001 tiene estado: En preparación'
        }
        
        send_url = reverse('notifications:send_notification')
        response = self.client.post(send_url, notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Verificar que se creó la notificación
        notification_id = response.data['notification_id']
        self.assertIsNotNone(notification_id)
        
        # 3. Obtener detalle de la notificación
        detail_url = reverse('notifications:notification_detail', kwargs={'pk': notification_id})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['user'], self.user.id)
        
        # 4. Verificar configuración
        settings_url = reverse('notifications:notification_settings')
        settings_response = self.client.get(settings_url)
        self.assertEqual(settings_response.status_code, status.HTTP_200_OK) 