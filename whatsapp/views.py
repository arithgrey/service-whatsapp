"""
Vistas para la aplicación de WhatsApp
Siguiendo las reglas del backend: Django 4.2.7, sin Redis innecesario, manejo de errores robusto
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import WhatsAppMessage, WhatsAppTemplate
from .serializers import (
    WhatsAppTemplateSerializer, WhatsAppMessageCreateSerializer,
    WhatsAppWebhookSerializer
)
from .services import whatsapp_service
from django.utils import timezone
from app.middleware import api_circuit_breaker
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

logger = logging.getLogger('whatsapp')


class SendTextMessageView(APIView):
    """Vista para enviar mensajes de texto"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = WhatsAppMessageCreateSerializer(data=request.data)
            if serializer.is_valid():
                # Enviar mensaje usando el servicio
                success, message = whatsapp_service.send_text_message(
                    phone_number=serializer.validated_data['phone_number'],
                    message=serializer.validated_data['message_content'],
                    order_id=serializer.validated_data.get('order_id')
                )
                
                if success:
                    return Response({
                        'success': True,
                        'message': message,
                        'data': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'error': message
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando mensaje de texto: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendTemplateMessageView(APIView):
    """Vista para enviar mensajes usando plantillas"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            template_name = request.data.get('template_name')
            variables = request.data.get('variables', {})
            order_id = request.data.get('order_id')
            
            if not all([phone_number, template_name]):
                return Response({
                    'success': False,
                    'error': 'phone_number y template_name son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar mensaje usando el servicio
            success, message = whatsapp_service.send_template_message(
                phone_number=phone_number,
                template_name=template_name,
                variables=variables,
                order_id=order_id
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'data': {
                        'phone_number': phone_number,
                        'template_name': template_name,
                        'variables': variables,
                        'order_id': order_id
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando mensaje de plantilla: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendOrderConfirmationView(APIView):
    """Vista para enviar confirmación de pedido"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            order_data = request.data.get('order_data', {})
            customer_name = request.data.get('customer_name')
            
            if not all([phone_number, order_data, customer_name]):
                return Response({
                    'success': False,
                    'error': 'phone_number, order_data y customer_name son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar confirmación usando el servicio
            success, message = whatsapp_service.send_order_confirmation(
                phone_number=phone_number,
                order_data=order_data,
                customer_name=customer_name
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'data': {
                        'phone_number': phone_number,
                        'order_id': order_data.get('id'),
                        'customer_name': customer_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando confirmación de pedido: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendOrderStatusUpdateView(APIView):
    """Vista para enviar actualización de estado del pedido"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            order_id = request.data.get('order_id')
            status = request.data.get('status')
            additional_info = request.data.get('additional_info')
            
            if not all([phone_number, order_id, status]):
                return Response({
                    'success': False,
                    'error': 'phone_number, order_id y status son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar actualización usando el servicio
            success, message = whatsapp_service.send_order_status_update(
                phone_number=phone_number,
                order_id=order_id,
                status=status,
                additional_info=additional_info
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'data': {
                        'phone_number': phone_number,
                        'order_id': order_id,
                        'status': status,
                        'additional_info': additional_info
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando actualización de estado: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vistas para plantillas
class WhatsAppTemplateListView(generics.ListAPIView):
    """Lista todas las plantillas de WhatsApp"""
    queryset = WhatsAppTemplate.objects.filter(is_active=True)
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        language = self.request.query_params.get('language')
        
        if category:
            queryset = queryset.filter(category=category)
        if language:
            queryset = queryset.filter(language=language)
            
        return queryset


class WhatsAppTemplateDetailView(generics.RetrieveAPIView):
    """Detalle de una plantilla específica"""
    queryset = WhatsAppTemplate.objects.all()
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]


class WhatsAppTemplateCreateView(generics.CreateAPIView):
    """Crear una nueva plantilla"""
    queryset = WhatsAppTemplate.objects.all()
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]


class WhatsAppTemplateUpdateView(generics.UpdateAPIView):
    """Actualizar una plantilla existente"""
    queryset = WhatsAppTemplate.objects.all()
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]


class WhatsAppTemplateDeleteView(generics.DestroyAPIView):
    """Eliminar una plantilla (marcar como inactiva)"""
    queryset = WhatsAppTemplate.objects.all()
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# Vistas para mensajes
class WhatsAppMessageListView(generics.ListAPIView):
    """Lista todos los mensajes de WhatsApp"""
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        phone_number = self.request.query_params.get('phone_number')
        status = self.request.query_params.get('status')
        order_id = self.request.query_params.get('order_id')
        
        if phone_number:
            queryset = queryset.filter(phone_number=phone_number)
        if status:
            queryset = queryset.filter(status=status)
        if order_id:
            queryset = queryset.filter(order_id=order_id)
            
        return queryset


class WhatsAppMessageDetailView(generics.RetrieveAPIView):
    """Detalle de un mensaje específico"""
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageCreateSerializer
    permission_classes = [IsAuthenticated]


class ResendMessageView(APIView):
    """Reenviar un mensaje fallido"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            message = WhatsAppMessage.objects.get(pk=pk)
            
            if message.status != 'failed':
                return Response({
                    'success': False,
                    'error': 'Solo se pueden reenviar mensajes fallidos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reenviar usando el servicio
            if message.template:
                success, result = whatsapp_service.send_template_message(
                    phone_number=message.phone_number,
                    template_name=message.template.name,
                    variables=message.metadata.get('variables', {}),
                    order_id=message.order_id
                )
            else:
                success, result = whatsapp_service.send_text_message(
                    phone_number=message.phone_number,
                    message=message.message_content,
                    order_id=message.order_id
                )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Mensaje reenviado exitosamente'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except WhatsAppMessage.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Mensaje no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error reenviando mensaje: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Webhook de WhatsApp
@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Maneja los webhooks de WhatsApp"""
    
    def get(self, request):
        """Verificación del webhook"""
        try:
            mode = request.GET.get('hub.mode')
            token = request.GET.get('hub.verify_token')
            challenge = request.GET.get('hub.challenge')
            
            if not all([mode, token, challenge]):
                return JsonResponse({'error': 'Parámetros faltantes'}, status=400)
            
            # Verificar webhook
            result = whatsapp_service.verify_webhook(mode, token, challenge)
            
            if result:
                return JsonResponse(result, content_type='text/plain')
            else:
                return JsonResponse({'error': 'Verificación fallida'}, status=403)
                
        except Exception as e:
            logger.error(f"Error verificando webhook: {str(e)}")
            return JsonResponse({'error': 'Error interno'}, status=500)
    
    def post(self, request):
        """Procesar webhook entrante"""
        try:
            # Procesar webhook usando el servicio
            success = whatsapp_service.process_webhook(request.body.decode('utf-8'))
            
            if success:
                return JsonResponse({'status': 'ok'})
            else:
                return JsonResponse({'error': 'Error procesando webhook'}, status=400)
                
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return JsonResponse({'error': 'Error interno'}, status=500)


# Vistas de utilidad
class ServiceStatusView(APIView):
    """Estado del servicio de WhatsApp"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Verificar configuración básica
            config_status = {
                'whatsapp_api_url': bool(whatsapp_service.api_url),
                'phone_number_id': bool(whatsapp_service.phone_number_id),
                'access_token': bool(whatsapp_service.access_token),
                'verify_token': bool(whatsapp_service.verify_token)
            }
            
            is_configured = all(config_status.values())
            
            return Response({
                'service': 'WhatsApp Notification Service',
                'status': 'active' if is_configured else 'inactive',
                'configured': is_configured,
                'configuration': config_status,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del servicio: {str(e)}")
            return Response({
                'service': 'WhatsApp Notification Service',
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageStatsView(APIView):
    """Estadísticas de mensajes"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Obtener estadísticas básicas
            total_messages = WhatsAppMessage.objects.count()
            successful_messages = WhatsAppMessage.objects.filter(
                status__in=['sent', 'delivered', 'read']
            ).count()
            failed_messages = WhatsAppMessage.objects.filter(status='failed').count()
            pending_messages = WhatsAppMessage.objects.filter(status='pending').count()
            
            # Estadísticas por tipo
            by_type = {}
            for message_type, _ in WhatsAppMessage.MESSAGE_TYPE_CHOICES:
                count = WhatsAppMessage.objects.filter(message_type=message_type).count()
                by_type[message_type] = count
            
            # Estadísticas por estado
            by_status = {}
            for status, _ in WhatsAppMessage.STATUS_CHOICES:
                count = WhatsAppMessage.objects.filter(status=status).count()
                by_status[status] = count
            
            return Response({
                'total_messages': total_messages,
                'successful_messages': successful_messages,
                'failed_messages': failed_messages,
                'pending_messages': pending_messages,
                'success_rate': (successful_messages / total_messages * 100) if total_messages > 0 else 0,
                'by_type': by_type,
                'by_status': by_status,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return Response({
                'error': 'Error obteniendo estadísticas'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['GET'])
def circuit_breaker_status(request):
    """Endpoint para obtener el estado del Circuit Breaker"""
    return Response({
        'current_state': str(api_circuit_breaker.current_state),
        'failure_count': api_circuit_breaker.fail_counter,
        'last_failure_time': None,  # pybreaker no expone este atributo
        'next_attempt_time': None,  # pybreaker no expone este atributo
    }) 


class SendOrderNotificationView(APIView):
    """Vista para enviar notificaciones de pedidos usando el nuevo servicio mejorado"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            order_data = request.data.get('order_data')
            notification_type = request.data.get('notification_type')
            customer_name = request.data.get('customer_name')
            
            # Validar datos requeridos
            if not all([phone_number, order_data, notification_type]):
                return Response({
                    'success': False,
                    'error': 'phone_number, order_data y notification_type son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar tipo de notificación
            valid_types = ['order_confirmation', 'order_status_update', 'order_delivered', 
                          'order_cancelled', 'payment_confirmed', 'shipping_update']
            
            if notification_type not in valid_types:
                return Response({
                    'success': False,
                    'error': f'Tipo de notificación inválido. Tipos válidos: {", ".join(valid_types)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar notificación usando el servicio mejorado
            success, message = whatsapp_service.send_order_notification(
                phone_number=phone_number,
                order_data=order_data,
                notification_type=notification_type,
                customer_name=customer_name
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'data': {
                        'phone_number': phone_number,
                        'notification_type': notification_type,
                        'order_id': order_data.get('id'),
                        'customer_name': customer_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando notificación de pedido: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendBulkOrderNotificationsView(APIView):
    """Vista para enviar múltiples notificaciones de pedidos en lote"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            notifications = request.data.get('notifications', [])
            
            if not notifications:
                return Response({
                    'success': False,
                    'error': 'La lista de notificaciones no puede estar vacía'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(notifications) > 100:  # Límite de 100 notificaciones por lote
                return Response({
                    'success': False,
                    'error': 'Máximo 100 notificaciones por lote'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar notificaciones en lote
            results = whatsapp_service.send_bulk_order_notifications(notifications)
            
            # Contar éxitos y fallos
            success_count = sum(1 for success, _ in results if success)
            failure_count = len(results) - success_count
            
            return Response({
                'success': True,
                'message': f'Procesadas {len(results)} notificaciones. Éxitos: {success_count}, Fallos: {failure_count}',
                'results': [
                    {'success': success, 'message': message} 
                    for success, message in results
                ]
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error enviando notificaciones en lote: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


class TestHolaJonView(APIView):
    """
    Vista de prueba para enviar un saludo de WhatsApp al número 5552967027
    Endpoint: GET /test/hola-jon
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación para pruebas
    
    @swagger_auto_schema(
        operation_description="Endpoint de prueba para enviar un saludo de WhatsApp",
        operation_summary="Prueba de envío de WhatsApp",
        responses={
            200: openapi.Response(
                description="Mensaje enviado exitosamente",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Mensaje de prueba enviado exitosamente",
                        "data": {
                            "phone_number": "5552967027",
                            "message_content": "¡Hola Jon! Este es un mensaje de prueba del servicio de WhatsApp.",
                            "message_id": "msg_123456789"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Error en el envío del mensaje",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Error enviando mensaje de prueba"
                    }
                }
            ),
            500: openapi.Response(
                description="Error interno del servidor",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Error interno del servidor"
                    }
                }
            )
        },
        tags=["Pruebas"]
    )
    def get(self, request):
        """
        Envía un mensaje de prueba de WhatsApp al número 5552967027
        """
        try:
            phone_number = "5552967027"
            message_content = "¡Hola Jon! Este es un mensaje de prueba del servicio de WhatsApp."
            
            # Enviar mensaje usando el servicio
            success, response_message = whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=message_content,
                order_id="TEST_HOLA_JON"
            )
            
            if success:
                logger.info(f"Mensaje de prueba enviado exitosamente a {phone_number}")
                return Response({
                    'success': True,
                    'message': 'Mensaje de prueba enviado exitosamente',
                    'data': {
                        'phone_number': phone_number,
                        'message_content': message_content,
                        'message_id': response_message if 'id' in response_message else 'N/A'
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Error enviando mensaje de prueba a {phone_number}: {response_message}")
                return Response({
                    'success': False,
                    'error': f'Error enviando mensaje de prueba: {response_message}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error inesperado en endpoint de prueba: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 