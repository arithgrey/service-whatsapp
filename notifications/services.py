"""
Servicios para la aplicación de notificaciones
"""

import logging
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Notification, NotificationTemplate, NotificationSettings
from whatsapp.services import whatsapp_service

logger = logging.getLogger('notifications')


class NotificationService:
    """Servicio principal para el manejo de notificaciones"""
    
    @staticmethod
    def send_notification(
        notification_type: str,
        recipient_data: Dict,
        content: str,
        template_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        scheduled_at: Optional[timezone.datetime] = None,
        created_by: Optional[User] = None
    ) -> Tuple[bool, str, Optional[Notification]]:
        """
        Envía una notificación individual
        
        Args:
            notification_type: Tipo de notificación
            recipient_data: Datos del destinatario
            content: Contenido de la notificación
            template_id: ID de la plantilla (opcional)
            metadata: Metadatos adicionales
            scheduled_at: Fecha programada (opcional)
            created_by: Usuario que crea la notificación
            
        Returns:
            Tuple con (éxito, mensaje, notificación)
        """
        try:
            # Crear la notificación en la base de datos
            notification = Notification.objects.create(
                recipient=str(recipient_data),
                channel=notification_type,
                notification_type=notification_type,
                content=content,
                template_id=template_id,
                metadata=metadata or {},
                scheduled_at=scheduled_at,
                created_by=created_by
            )
            
            # Si no está programada, enviar inmediatamente
            if not scheduled_at:
                success, message = NotificationService._send_immediate_notification(
                    notification, recipient_data
                )
                
                if success:
                    notification.mark_as_sent()
                    return True, message, notification
                else:
                    notification.mark_as_failed(message)
                    return False, message, notification
            
            return True, "Notificación programada correctamente", notification
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return False, f"Error interno: {str(e)}", None
    
    @staticmethod
    def send_batch_notifications(
        notifications_data: List[Dict],
        created_by: Optional[User] = None
    ) -> Tuple[bool, str, List[Notification]]:
        """
        Envía múltiples notificaciones en lote
        
        Args:
            notifications_data: Lista de datos de notificaciones
            created_by: Usuario que crea las notificaciones
            
        Returns:
            Tuple con (éxito, mensaje, lista de notificaciones)
        """
        try:
            created_notifications = []
            failed_count = 0
            
            for notification_data in notifications_data:
                success, message, notification = NotificationService.send_notification(
                    notification_type=notification_data.get('type'),
                    recipient_data=notification_data.get('recipient'),
                    content=notification_data.get('content'),
                    template_id=notification_data.get('template_id'),
                    metadata=notification_data.get('metadata'),
                    scheduled_at=notification_data.get('scheduled_at'),
                    created_by=created_by
                )
                
                if success and notification:
                    created_notifications.append(notification)
                else:
                    failed_count += 1
                    logger.warning(f"Notificación fallida: {message}")
            
            if failed_count == 0:
                return True, f"Todas las notificaciones enviadas ({len(created_notifications)})", created_notifications
            elif created_notifications:
                return True, f"Notificaciones enviadas: {len(created_notifications)}, fallidas: {failed_count}", created_notifications
            else:
                return False, f"Todas las notificaciones fallaron ({failed_count})", []
                
        except Exception as e:
            logger.error(f"Error enviando notificaciones en lote: {str(e)}")
            return False, f"Error interno: {str(e)}", []
    
    @staticmethod
    def schedule_notification(
        template_id: int,
        recipients: List[str],
        scheduled_at: timezone.datetime,
        metadata: Optional[Dict] = None,
        created_by: Optional[User] = None
    ) -> Tuple[bool, str, List[Notification]]:
        """
        Programa notificaciones para envío futuro
        
        Args:
            template_id: ID de la plantilla a usar
            recipients: Lista de destinatarios
            scheduled_at: Fecha y hora para el envío
            metadata: Metadatos adicionales
            created_by: Usuario que programa las notificaciones
            
        Returns:
            Tuple con (éxito, mensaje, lista de notificaciones)
        """
        try:
            # Verificar que la plantilla existe y está activa
            try:
                template = NotificationTemplate.objects.get(
                    id=template_id, 
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                return False, "Plantilla no encontrada o inactiva", []
            
            # Crear notificaciones programadas
            created_notifications = []
            for recipient in recipients:
                notification = Notification.objects.create(
                    recipient=recipient,
                    channel='whatsapp',  # Por defecto WhatsApp
                    notification_type=template.notification_type,
                    title=template.title,
                    content=template.content,
                    template=template,
                    scheduled_at=scheduled_at,
                    metadata=metadata or {},
                    created_by=created_by
                )
                created_notifications.append(notification)
            
            return True, f"Notificaciones programadas: {len(created_notifications)}", created_notifications
            
        except Exception as e:
            logger.error(f"Error programando notificaciones: {str(e)}")
            return False, f"Error interno: {str(e)}", []
    
    @staticmethod
    def cancel_notification(notification_id: int) -> Tuple[bool, str]:
        """
        Cancela una notificación programada
        
        Args:
            notification_id: ID de la notificación
            
        Returns:
            Tuple con (éxito, mensaje)
        """
        try:
            notification = Notification.objects.get(id=notification_id)
            
            if notification.status != 'pending':
                return False, "Solo se pueden cancelar notificaciones pendientes"
            
            notification.cancel()
            return True, "Notificación cancelada correctamente"
            
        except Notification.DoesNotExist:
            return False, "Notificación no encontrada"
        except Exception as e:
            logger.error(f"Error cancelando notificación: {str(e)}")
            return False, f"Error interno: {str(e)}"
    
    @staticmethod
    def get_notification_stats(
        user: Optional[User] = None,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """
        Obtiene estadísticas de notificaciones
        
        Args:
            user: Usuario para filtrar (opcional)
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            queryset = Notification.objects.all()
            
            if user:
                queryset = queryset.filter(created_by=user)
            
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)
            
            total = queryset.count()
            sent = queryset.filter(status='sent').count()
            delivered = queryset.filter(status='delivered').count()
            failed = queryset.filter(status='failed').count()
            pending = queryset.filter(status='pending').count()
            cancelled = queryset.filter(status='cancelled').count()
            
            return {
                'total': total,
                'sent': sent,
                'delivered': delivered,
                'failed': failed,
                'pending': pending,
                'cancelled': cancelled,
                'success_rate': (sent + delivered) / total * 100 if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    @staticmethod
    def _send_immediate_notification(
        notification: Notification,
        recipient_data: Dict
    ) -> Tuple[bool, str]:
        """
        Envía una notificación inmediata según el canal
        
        Args:
            notification: Objeto de notificación
            recipient_data: Datos del destinatario
            
        Returns:
            Tuple con (éxito, mensaje)
        """
        try:
            if notification.channel == 'whatsapp':
                phone_number = recipient_data.get('phone_number')
                if not phone_number:
                    return False, "Número de teléfono requerido para WhatsApp"
                
                success, message = whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=notification.content,
                    order_id=notification.metadata.get('order_id')
                )
                
                return success, message
                
            elif notification.channel == 'email':
                # TODO: Implementar envío de email
                return False, "Canal de email no implementado aún"
                
            elif notification.channel == 'sms':
                # TODO: Implementar envío de SMS
                return False, "Canal de SMS no implementado aún"
                
            elif notification.channel == 'push':
                # TODO: Implementar notificaciones push
                return False, "Canal de push no implementado aún"
                
            else:
                return False, f"Canal no soportado: {notification.channel}"
                
        except Exception as e:
            logger.error(f"Error enviando notificación inmediata: {str(e)}")
            return False, f"Error interno: {str(e)}"


class NotificationTemplateService:
    """Servicio para el manejo de plantillas de notificación"""
    
    @staticmethod
    def create_template(
        name: str,
        notification_type: str,
        title: str,
        content: str,
        created_by: User
    ) -> Tuple[bool, str, Optional[NotificationTemplate]]:
        """
        Crea una nueva plantilla de notificación
        
        Args:
            name: Nombre de la plantilla
            notification_type: Tipo de notificación
            title: Título de la notificación
            content: Contenido con variables
            created_by: Usuario que crea la plantilla
            
        Returns:
            Tuple con (éxito, mensaje, plantilla)
        """
        try:
            # Verificar que no exista una plantilla con el mismo nombre y tipo
            if NotificationTemplate.objects.filter(
                name=name, 
                notification_type=notification_type
            ).exists():
                return False, "Ya existe una plantilla con ese nombre y tipo", None
            
            template = NotificationTemplate.objects.create(
                name=name,
                notification_type=notification_type,
                title=title,
                content=content,
                created_by=created_by
            )
            
            return True, "Plantilla creada correctamente", template
            
        except Exception as e:
            logger.error(f"Error creando plantilla: {str(e)}")
            return False, f"Error interno: {str(e)}", None
    
    @staticmethod
    def update_template(
        template_id: int,
        **kwargs
    ) -> Tuple[bool, str, Optional[NotificationTemplate]]:
        """
        Actualiza una plantilla existente
        
        Args:
            template_id: ID de la plantilla
            **kwargs: Campos a actualizar
            
        Returns:
            Tuple con (éxito, mensaje, plantilla)
        """
        try:
            template = NotificationTemplate.objects.get(id=template_id)
            
            for field, value in kwargs.items():
                if hasattr(template, field):
                    setattr(template, field, value)
            
            template.save()
            return True, "Plantilla actualizada correctamente", template
            
        except NotificationTemplate.DoesNotExist:
            return False, "Plantilla no encontrada", None
        except Exception as e:
            logger.error(f"Error actualizando plantilla: {str(e)}")
            return False, f"Error interno: {str(e)}", None
    
    @staticmethod
    def get_active_templates(notification_type: Optional[str] = None) -> List[NotificationTemplate]:
        """
        Obtiene plantillas activas
        
        Args:
            notification_type: Tipo de notificación para filtrar (opcional)
            
        Returns:
            Lista de plantillas activas
        """
        queryset = NotificationTemplate.objects.filter(is_active=True)
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset.order_by('name')
    
    @staticmethod
    def render_template(
        template: NotificationTemplate,
        variables: Dict[str, str]
    ) -> str:
        """
        Renderiza una plantilla con variables
        
        Args:
            template: Plantilla a renderizar
            variables: Variables para sustituir
            
        Returns:
            Contenido renderizado
        """
        content = template.content
        
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, str(var_value))
        
        return content 