"""
Vistas para la aplicación de notificaciones
Siguiendo las reglas del backend: Django 4.2.7, sin Redis innecesario, manejo de errores robusto
"""

import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from whatsapp.services import whatsapp_service

logger = logging.getLogger('notifications')


class SendNotificationView(APIView):
    """Vista para enviar notificaciones individuales"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            notification_type = request.data.get('type')
            recipient_data = request.data.get('recipient')
            content = request.data.get('content')
            metadata = request.data.get('metadata', {})
            
            if not all([notification_type, recipient_data, content]):
                return Response({
                    'success': False,
                    'error': 'type, recipient y content son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar notificación según el tipo
            if notification_type == 'whatsapp':
                success, message = whatsapp_service.send_text_message(
                    phone_number=recipient_data.get('phone_number'),
                    message=content,
                    order_id=metadata.get('order_id')
                )
            else:
                return Response({
                    'success': False,
                    'error': f'Tipo de notificación no soportado: {notification_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'data': {
                        'type': notification_type,
                        'recipient': recipient_data,
                        'content': content
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendBatchNotificationView(APIView):
    """Vista para enviar notificaciones en lote"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            notifications = request.data.get('notifications', [])
            
            if not notifications:
                return Response({
                    'success': False,
                    'error': 'La lista de notificaciones no puede estar vacía'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            results = []
            for notification in notifications:
                try:
                    notification_type = notification.get('type')
                    recipient_data = notification.get('recipient')
                    content = notification.get('content')
                    metadata = notification.get('metadata', {})
                    
                    if notification_type == 'whatsapp':
                        success, message = whatsapp_service.send_text_message(
                            phone_number=recipient_data.get('phone_number'),
                            message=content,
                            order_id=metadata.get('order_id')
                        )
                    else:
                        success, message = False, f'Tipo no soportado: {notification_type}'
                    
                    results.append({
                        'recipient': recipient_data,
                        'success': success,
                        'message': message
                    })
                    
                except Exception as e:
                    results.append({
                        'recipient': notification.get('recipient', {}),
                        'success': False,
                        'message': f'Error: {str(e)}'
                    })
            
            # Contar resultados
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            return Response({
                'success': True,
                'message': f'Procesadas {len(results)} notificaciones',
                'results': results,
                'summary': {
                    'total': len(results),
                    'successful': successful,
                    'failed': failed
                }
            })
            
        except Exception as e:
            logger.error(f"Error enviando notificaciones en lote: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleNotificationView(APIView):
    """Vista para programar notificaciones futuras"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Por ahora, implementación básica
            # En el futuro se puede integrar con Celery o similar
            return Response({
                'success': False,
                'error': 'Programación de notificaciones no implementada aún'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
        except Exception as e:
            logger.error(f"Error programando notificación: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationListView(APIView):
    """Vista para listar notificaciones"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Por ahora, redirigir a la lista de mensajes de WhatsApp
            # En el futuro se puede implementar una vista unificada
            return Response({
                'success': True,
                'message': 'Use /api/whatsapp/messages/ para ver notificaciones'
            })
            
        except Exception as e:
            logger.error(f"Error listando notificaciones: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationDetailView(APIView):
    """Vista para detalle de notificación"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            # Por ahora, redirigir al detalle de mensaje de WhatsApp
            return Response({
                'success': True,
                'message': f'Use /api/whatsapp/messages/{pk}/ para ver detalles'
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo detalle de notificación: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelNotificationView(APIView):
    """Vista para cancelar notificaciones programadas"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            # Por ahora, implementación básica
            return Response({
                'success': False,
                'error': 'Cancelación de notificaciones no implementada aún'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
        except Exception as e:
            logger.error(f"Error cancelando notificación: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationSettingsView(APIView):
    """Vista para configurar notificaciones"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Configuración básica del servicio
            settings = {
                'whatsapp_enabled': bool(whatsapp_service.phone_number_id and whatsapp_service.access_token),
                'supported_types': ['whatsapp'],
                'default_language': 'es',
                'timezone': 'America/Mexico_City'
            }
            
            return Response({
                'success': True,
                'settings': settings
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        try:
            # Por ahora, solo lectura
            return Response({
                'success': False,
                'error': 'Modificación de configuración no implementada aún'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
        except Exception as e:
            logger.error(f"Error modificando configuración: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationTemplateListView(APIView):
    """Vista para listar plantillas de notificaciones"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Redirigir a las plantillas de WhatsApp
            return Response({
                'success': True,
                'message': 'Use /api/whatsapp/templates/ para ver plantillas'
            })
            
        except Exception as e:
            logger.error(f"Error listando plantillas: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 