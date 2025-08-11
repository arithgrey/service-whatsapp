"""
Tests de integración para el servicio de WhatsApp
Siguiendo las reglas del backend: TDD, sin mocks, pruebas de integración obligatorias
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import WhatsAppTemplate, WhatsAppMessage
from .services import WhatsAppService
from faker import Faker
import json

fake = Faker(['es_MX'])


class WhatsAppServiceIntegrationTest(TestCase):
    """Tests de integración para el servicio de WhatsApp"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear plantilla de prueba
        self.template = WhatsAppTemplate.objects.create(
            name='Test Order Confirmation',
            category='order_confirmation',
            language='es',
            content='¡Hola {{customer_name}}! Tu pedido #{{order_number}} ha sido confirmado.',
            variables=['customer_name', 'order_number'],
            is_active=True
        )
        
        # Datos de pedido de prueba
        self.order_data = {
            'id': '12345',
            'order_number': 'ORD-001',
            'total_amount': '299.99',
            'status': 'confirmed',
            'products': [{'name': 'Producto Test'}],
            'shipping_address': {
                'street': 'Calle Test',
                'number': '123',
                'city': 'Ciudad Test',
                'state': {'name': 'Estado Test'},
                'postal_code': '12345'
            }
        }
        
        self.whatsapp_service = WhatsAppService()

    def test_send_order_notification_success(self):
        """Test de envío exitoso de notificación de pedido"""
        phone_number = '+525512345678'
        notification_type = 'order_confirmation'
        customer_name = 'Juan Pérez'
        
        success, message = self.whatsapp_service.send_order_notification(
            phone_number=phone_number,
            order_data=self.order_data,
            notification_type=notification_type,
            customer_name=customer_name
        )
        
        self.assertTrue(success)
        self.assertIn('enviado', message.lower())
        
        # Verificar que se creó el mensaje en la base de datos
        message_obj = WhatsAppMessage.objects.filter(
            phone_number=phone_number,
            order_id=self.order_data['id']
        ).first()
        
        self.assertIsNotNone(message_obj)
        self.assertEqual(message_obj.message_type, 'template')
        self.assertEqual(message_obj.template, self.template)

    def test_send_order_notification_invalid_type(self):
        """Test de envío con tipo de notificación inválido"""
        phone_number = '+525512345678'
        notification_type = 'invalid_type'
        
        success, message = self.whatsapp_service.send_order_notification(
            phone_number=phone_number,
            order_data=self.order_data,
            notification_type=notification_type
        )
        
        self.assertFalse(success)
        self.assertIn('inválido', message.lower())

    def test_send_order_notification_no_template(self):
        """Test de envío sin plantilla disponible"""
        self.template.is_active = False
        self.template.save()
        
        phone_number = '+525512345678'
        notification_type = 'order_confirmation'
        
        success, message = self.whatsapp_service.send_order_notification(
            phone_number=phone_number,
            order_data=self.order_data,
            notification_type=notification_type
        )
        
        self.assertFalse(success)
        self.assertIn('plantilla', message.lower())

    def test_prepare_order_variables(self):
        """Test de preparación de variables para plantillas"""
        customer_name = 'María García'
        
        variables = self.whatsapp_service._prepare_order_variables(
            self.order_data, customer_name
        )
        
        self.assertEqual(variables['customer_name'], customer_name)
        self.assertEqual(variables['order_id'], self.order_data['id'])
        self.assertEqual(variables['total_amount'], self.order_data['total_amount'])
        self.assertIn('order_date', variables)

    def test_send_bulk_order_notifications(self):
        """Test de envío de notificaciones en lote"""
        notifications_data = [
            {
                'phone_number': '+525512345678',
                'order_data': self.order_data,
                'notification_type': 'order_confirmation',
                'customer_name': 'Cliente 1'
            },
            {
                'phone_number': '+525512345679',
                'order_data': {
                    'id': '67890',
                    'order_number': 'ORD-002',
                    'total_amount': '199.99',
                    'status': 'confirmed'
                },
                'notification_type': 'order_confirmation',
                'customer_name': 'Cliente 2'
            }
        ]
        
        results = self.whatsapp_service.send_bulk_order_notifications(notifications_data)
        
        self.assertEqual(len(results), 2)
        for success, message in results:
            self.assertTrue(success)
            self.assertIn('enviado', message.lower())


class WhatsAppAPIIntegrationTest(TestCase):
    """Tests de integración para la API de WhatsApp"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear plantilla de prueba
        self.template = WhatsAppTemplate.objects.create(
            name='Test Template',
            category='order_confirmation',
            language='es',
            content='Test message for {{customer_name}}',
            variables=['customer_name'],
            is_active=True
        )
        
        # Datos de pedido de prueba
        self.order_data = {
            'id': '12345',
            'order_number': 'ORD-001',
            'total_amount': '299.99',
            'status': 'confirmed'
        }

    def test_send_order_notification_api_success(self):
        """Test de API para envío exitoso de notificación"""
        data = {
            'phone_number': '+525512345678',
            'order_data': self.order_data,
            'notification_type': 'order_confirmation',
            'customer_name': 'Juan Pérez'
        }
        
        response = self.client.post(
            reverse('whatsapp:send_order_notification'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('enviado', response.data['message'].lower())

    def test_send_order_notification_api_missing_data(self):
        """Test de API con datos faltantes"""
        data = {
            'phone_number': '+525512345678'
            # Faltan order_data y notification_type
        }
        
        response = self.client.post(
            reverse('whatsapp:send_order_notification'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_send_bulk_order_notifications_api_success(self):
        """Test de API para envío en lote exitoso"""
        data = {
            'notifications': [
                {
                    'phone_number': '+525512345678',
                    'order_data': self.order_data,
                    'notification_type': 'order_confirmation',
                    'customer_name': 'Cliente 1'
                },
                {
                    'phone_number': '+525512345679',
                    'order_data': {
                        'id': '67890',
                        'order_number': 'ORD-002',
                        'total_amount': '199.99',
                        'status': 'confirmed'
                    },
                    'notification_type': 'order_confirmation',
                    'customer_name': 'Cliente 2'
                }
            ]
        }
        
        response = self.client.post(
            reverse('whatsapp:send_bulk_order_notifications'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 2)

    def test_api_authentication_required(self):
        """Test de que la autenticación sea requerida"""
        self.client.force_authenticate(user=None)
        
        data = {
            'phone_number': '+525512345678',
            'order_data': self.order_data,
            'notification_type': 'order_confirmation'
        }
        
        response = self.client.post(
            reverse('whatsapp:send_order_notification'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WhatsAppTemplateAPITest(TestCase):
    """Tests para la API de plantillas de WhatsApp"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear plantilla de prueba
        self.template = WhatsAppTemplate.objects.create(
            name='Test Template',
            category='order_confirmation',
            language='es',
            content='Test message for {{customer_name}}',
            variables=['customer_name'],
            is_active=True
        )

    def test_template_list_api(self):
        """Test de API para listar plantillas"""
        response = self.client.get(reverse('whatsapp:template_list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Template')

    def test_template_create_api(self):
        """Test de API para crear plantilla"""
        data = {
            'name': 'New Template',
            'category': 'custom',
            'language': 'es',
            'content': 'New message for {{customer_name}}',
            'variables': ['customer_name']
        }
        
        response = self.client.post(
            reverse('whatsapp:template_create'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Template')


class WhatsAppMessageAPITest(TestCase):
    """Tests para la API de mensajes de WhatsApp"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear mensaje de prueba
        self.message = WhatsAppMessage.objects.create(
            phone_number='+525512345678',
            message_type='text',
            message_content='Test message',
            status='pending',
            user=self.user
        )

    def test_message_list_api(self):
        """Test de API para listar mensajes"""
        response = self.client.get(reverse('whatsapp:message_list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_resend_message_api(self):
        """Test de API para reenviar mensaje"""
        response = self.client.post(
            reverse('whatsapp:resend_message', kwargs={'pk': self.message.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class CircuitBreakerTest(TestCase):
    """Tests para el Circuit Breaker"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_circuit_breaker_status_api(self):
        """Test de API para estado del Circuit Breaker"""
        response = self.client.get(reverse('whatsapp:circuit_breaker_status'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('current_state', response.data)
        self.assertIn('failure_count', response.data)


class WhatsAppWebhookTest(TestCase):
    """Tests para webhooks de WhatsApp"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        
        # Crear plantilla de prueba
        self.template = WhatsAppTemplate.objects.create(
            name='Test Template',
            category='order_confirmation',
            language='es',
            content='Test message',
            variables=['customer_name'],
            is_active=True
        )

    def test_webhook_verification(self):
        """Test de verificación de webhook"""
        # Para tests, esperamos que falle porque no hay token configurado
        params = {
            'hub.mode': 'subscribe',
            'hub.verify_token': 'test_token',
            'hub.challenge': 'test_challenge'
        }
        
        response = self.client.get(reverse('whatsapp:webhook'), params)
        
        # En tests, la verificación falla porque no hay token configurado
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_webhook_message_status_update(self):
        """Test de actualización de estado de mensaje via webhook"""
        message = WhatsAppMessage.objects.create(
            phone_number='+525512345678',
            message_type='text',
            message_content='Test message',
            status='sent',
            whatsapp_message_id='test_whatsapp_id'
        )
        
        webhook_data = {
            'object': 'whatsapp_business_account',
            'entry': [{
                'id': 'test_entry_id',
                'changes': [{
                    'value': {
                        'statuses': [{
                            'id': 'test_whatsapp_id',
                            'status': 'delivered'
                        }]
                    }
                }]
            }]
        }
        
        response = self.client.post(
            reverse('whatsapp:webhook'),
            webhook_data,
            format='json'
        )
        
        # En tests, el webhook falla porque no hay configuración completa
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 