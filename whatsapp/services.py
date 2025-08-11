"""
Servicio de WhatsApp para enviar notificaciones
Siguiendo las reglas del backend: sin Redis innecesario, manejo de errores robusto
"""

import requests
import logging
from django.conf import settings
from django.utils import timezone
from .models import WhatsAppMessage, WhatsAppTemplate
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('whatsapp')


class WhatsAppService:
    """
    Servicio principal para manejar notificaciones de WhatsApp
    """
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        
        if not all([self.phone_number_id, self.access_token]):
            logger.warning("Configuración de WhatsApp incompleta")
    
    def send_text_message(self, phone_number: str, message: str, order_id: str = None) -> Tuple[bool, str]:
        """
        Envía un mensaje de texto simple
        
        Args:
            phone_number: Número de teléfono del destinatario
            message: Contenido del mensaje
            order_id: ID del pedido relacionado
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje o error)
        """
        try:
            # Crear registro del mensaje
            whatsapp_message = WhatsAppMessage.objects.create(
                phone_number=phone_number,
                message_type='text',
                message_content=message,
                order_id=order_id,
                status='pending'
            )
            
            # Preparar payload para WhatsApp API
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": message}
            }
            
            # Enviar mensaje
            success, response_data = self._send_to_whatsapp_api(payload)
            
            if success:
                whatsapp_message.mark_as_sent(response_data.get('id', ''))
                logger.info(f"Mensaje de texto enviado exitosamente: {whatsapp_message.id}")
                return True, "Mensaje enviado exitosamente"
            else:
                whatsapp_message.mark_as_failed(response_data)
                logger.error(f"Error enviando mensaje de texto: {response_data}")
                return False, f"Error enviando mensaje: {response_data}"
                
        except Exception as e:
            logger.error(f"Error inesperado enviando mensaje de texto: {str(e)}")
            return False, f"Error inesperado: {str(e)}"
    
    def send_template_message(self, phone_number: str, template_name: str, 
                            variables: Dict[str, str], order_id: str = None) -> Tuple[bool, str]:
        """
        Envía un mensaje usando una plantilla predefinida
        
        Args:
            phone_number: Número de teléfono del destinatario
            template_name: Nombre de la plantilla a usar
            variables: Diccionario de variables para la plantilla
            order_id: ID del pedido relacionado
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje o error)
        """
        try:
            # Obtener la plantilla
            template = WhatsAppTemplate.objects.filter(
                name=template_name,
                is_active=True
            ).first()
            
            if not template:
                error_msg = f"Plantilla '{template_name}' no encontrada o inactiva"
                logger.error(error_msg)
                return False, error_msg
            
            # Validar variables
            missing_vars = set(template.variables) - set(variables.keys())
            if missing_vars:
                error_msg = f"Variables faltantes para la plantilla: {', '.join(missing_vars)}"
                logger.error(error_msg)
                return False, error_msg
            
            # Crear registro del mensaje
            whatsapp_message = WhatsAppMessage.objects.create(
                phone_number=phone_number,
                message_type='template',
                message_content=template.content,
                template=template,
                order_id=order_id,
                metadata={'variables': variables},
                status='pending'
            )
            
            # Preparar payload para WhatsApp API
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": template.language
                    },
                    "components": self._prepare_template_components(template, variables)
                }
            }
            
            # Enviar mensaje
            success, response_data = self._send_to_whatsapp_api(payload)
            
            if success:
                whatsapp_message.mark_as_sent(response_data.get('id', ''))
                logger.info(f"Mensaje de plantilla enviado exitosamente: {whatsapp_message.id}")
                return True, "Mensaje de plantilla enviado exitosamente"
            else:
                whatsapp_message.mark_as_failed(response_data)
                logger.error(f"Error enviando mensaje de plantilla: {response_data}")
                return False, f"Error enviando mensaje de plantilla: {response_data}"
                
        except Exception as e:
            logger.error(f"Error inesperado enviando mensaje de plantilla: {str(e)}")
            return False, f"Error inesperado: {str(e)}"
    
    def send_order_notification(self, phone_number: str, order_data: Dict, 
                               notification_type: str, customer_name: str = None) -> Tuple[bool, str]:
        """
        Envía notificación de pedido basada en el tipo especificado
        
        Args:
            phone_number: Número de teléfono del destinatario
            order_data: Datos completos del pedido
            notification_type: Tipo de notificación (order_confirmation, status_update, etc.)
            customer_name: Nombre del cliente
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje o error)
        """
        try:
            # Validar tipo de notificación
            valid_types = ['order_confirmation', 'order_status_update', 'order_delivered', 
                          'order_cancelled', 'payment_confirmed', 'shipping_update']
            
            if notification_type not in valid_types:
                error_msg = f"Tipo de notificación inválido: {notification_type}"
                logger.error(error_msg)
                return False, error_msg
            
            # Obtener plantilla correspondiente
            template = WhatsAppTemplate.objects.filter(
                category=notification_type,
                is_active=True
            ).first()
            
            if not template:
                error_msg = f"No hay plantilla activa para: {notification_type}"
                logger.error(error_msg)
                return False, error_msg
            
            # Preparar variables para la plantilla
            variables = self._prepare_order_variables(order_data, customer_name)
            
            # Enviar mensaje usando plantilla
            return self.send_template_message(
                phone_number=phone_number,
                template_name=template.name,
                variables=variables,
                order_id=order_data.get('id')
            )
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pedido: {str(e)}")
            return False, f"Error enviando notificación: {str(e)}"
    
    def send_bulk_order_notifications(self, notifications_data: List[Dict]) -> List[Tuple[bool, str]]:
        """
        Envía múltiples notificaciones de pedidos en lote
        
        Args:
            notifications_data: Lista de diccionarios con datos de notificaciones
            
        Returns:
            List[Tuple[bool, str]]: Lista de resultados (éxito, mensaje)
        """
        results = []
        
        for notification in notifications_data:
            try:
                phone_number = notification.get('phone_number')
                order_data = notification.get('order_data')
                notification_type = notification.get('notification_type')
                customer_name = notification.get('customer_name')
                
                if not all([phone_number, order_data, notification_type]):
                    results.append((False, "Datos incompletos para notificación"))
                    continue
                
                success, message = self.send_order_notification(
                    phone_number=phone_number,
                    order_data=order_data,
                    notification_type=notification_type,
                    customer_name=customer_name
                )
                
                results.append((success, message))
                
            except Exception as e:
                logger.error(f"Error en notificación en lote: {str(e)}")
                results.append((False, f"Error: {str(e)}"))
        
        return results

    def _prepare_order_variables(self, order_data: Dict, customer_name: str = None) -> Dict[str, str]:
        """
        Prepara las variables para las plantillas de pedidos
        
        Args:
            order_data: Datos del pedido
            customer_name: Nombre del cliente
            
        Returns:
            Dict[str, str]: Variables formateadas para la plantilla
        """
        variables = {}
        
        try:
            # Información básica del pedido
            variables['order_id'] = str(order_data.get('id', ''))
            variables['order_number'] = str(order_data.get('order_number', ''))
            variables['order_date'] = order_data.get('created_at', '')
            variables['total_amount'] = str(order_data.get('total_amount', '0.00'))
            
            # Información del cliente
            if customer_name:
                variables['customer_name'] = customer_name
            else:
                variables['customer_name'] = order_data.get('customer_name', 'Cliente')
            
            # Información de envío
            shipping_address = order_data.get('shipping_address', {})
            if shipping_address:
                variables['shipping_address'] = self._format_address(shipping_address)
            
            # Estado del pedido
            variables['order_status'] = order_data.get('status', 'Pendiente')
            
            # Información de productos
            products = order_data.get('products', [])
            if products:
                variables['product_count'] = str(len(products))
                variables['main_product'] = products[0].get('name', 'Producto') if products else 'Producto'
            
            # Información de pago
            payment_info = order_data.get('payment_info', {})
            if payment_info:
                variables['payment_method'] = payment_info.get('method', 'No especificado')
                variables['payment_status'] = payment_info.get('status', 'Pendiente')
            
        except Exception as e:
            logger.error(f"Error preparando variables del pedido: {str(e)}")
            # Variables por defecto en caso de error
            variables = {
                'order_id': str(order_data.get('id', 'N/A')),
                'customer_name': customer_name or 'Cliente',
                'order_status': 'Pendiente'
            }
        
        return variables
    
    def send_order_confirmation(self, phone_number: str, order_data: Dict, 
                              customer_name: str) -> Tuple[bool, str]:
        """
        Envía confirmación de pedido usando plantilla
        
        Args:
            phone_number: Número de teléfono del cliente
            order_data: Datos del pedido
            customer_name: Nombre del cliente
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje o error)
        """
        try:
            # Preparar variables para la plantilla
            variables = {
                'customer_name': customer_name,
                'order_id': str(order_data.get('id', '')),
                'order_total': f"${order_data.get('total', 0):.2f}",
                'order_date': order_data.get('created_at', '').strftime('%d/%m/%Y') if order_data.get('created_at') else '',
                'delivery_address': self._format_address(order_data.get('shipping_address', {})),
                'estimated_delivery': '2-3 días hábiles'
            }
            
            # Enviar mensaje usando plantilla
            return self.send_template_message(
                phone_number=phone_number,
                template_name='order_confirmation',
                variables=variables,
                order_id=str(order_data.get('id', ''))
            )
            
        except Exception as e:
            logger.error(f"Error enviando confirmación de pedido: {str(e)}")
            return False, f"Error enviando confirmación: {str(e)}"
    
    def send_order_status_update(self, phone_number: str, order_id: str, 
                               status: str, additional_info: str = None) -> Tuple[bool, str]:
        """
        Envía actualización de estado del pedido
        
        Args:
            phone_number: Número de teléfono del cliente
            order_id: ID del pedido
            status: Nuevo estado del pedido
            additional_info: Información adicional opcional
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje o error)
        """
        try:
            # Mapear estados a plantillas
            status_template_map = {
                'payment_confirmed': 'payment_confirmed',
                'preparing': 'order_status_update',
                'ready_for_shipping': 'order_status_update',
                'in_transit': 'shipping_update',
                'delivered': 'order_delivered',
                'cancelled': 'order_cancelled'
            }
            
            template_name = status_template_map.get(status, 'order_status_update')
            
            # Preparar variables
            status_display = dict(Order.STATUS_CHOICES).get(status, status)
            variables = {
                'order_id': order_id,
                'status': status_display,
                'additional_info': additional_info or '',
                'update_time': timezone.now().strftime('%d/%m/%Y %H:%M')
            }
            
            # Enviar mensaje
            return self.send_template_message(
                phone_number=phone_number,
                template_name=template_name,
                variables=variables,
                order_id=order_id
            )
            
        except Exception as e:
            logger.error(f"Error enviando actualización de estado: {str(e)}")
            return False, f"Error enviando actualización: {str(e)}"
    
    def _send_to_whatsapp_api(self, payload: Dict) -> Tuple[bool, Dict]:
        """
        Envía payload a la API de WhatsApp
        
        Args:
            payload: Datos a enviar
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta o error)
        """
        try:
            if not all([self.phone_number_id, self.access_token]):
                return False, "Configuración de WhatsApp incompleta"
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                return True, response_data
            else:
                error_data = {
                    'status_code': response.status_code,
                    'error': response.text,
                    'payload': payload
                }
                logger.error(f"Error en API de WhatsApp: {error_data}")
                return False, error_data
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout en la API de WhatsApp"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Error de conexión con WhatsApp API: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado en WhatsApp API: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _prepare_template_components(self, template: WhatsAppTemplate, 
                                   variables: Dict[str, str]) -> List[Dict]:
        """
        Prepara los componentes de la plantilla para WhatsApp API
        
        Args:
            template: Plantilla a usar
            variables: Variables para reemplazar
            
        Returns:
            List[Dict]: Componentes de la plantilla
        """
        components = []
        
        # Agregar componente de texto con variables
        if template.variables:
            text_component = {
                "type": "body",
                "parameters": []
            }
            
            for var_name in template.variables:
                if var_name in variables:
                    text_component["parameters"].append({
                        "type": "text",
                        "text": variables[var_name]
                    })
            
            if text_component["parameters"]:
                components.append(text_component)
        
        return components
    
    def _format_address(self, address_data: Dict) -> str:
        """
        Formatea la dirección para el mensaje
        
        Args:
            address_data: Datos de la dirección
            
        Returns:
            str: Dirección formateada
        """
        if not address_data:
            return "No especificada"
        
        parts = []
        if address_data.get('street'):
            parts.append(address_data['street'])
        if address_data.get('number'):
            parts.append(str(address_data['number']))
        if address_data.get('colony'):
            parts.append(address_data['colony'])
        if address_data.get('city'):
            parts.append(address_data['city'])
        if address_data.get('state'):
            parts.append(address_data['state'].get('name', ''))
        if address_data.get('postal_code'):
            parts.append(address_data['postal_code'])
        
        return ', '.join(filter(None, parts))
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica el webhook de WhatsApp
        
        Args:
            mode: Modo de verificación
            token: Token de verificación
            challenge: Desafío de verificación
            
        Returns:
            Optional[str]: Challenge si la verificación es exitosa
        """
        if mode == 'subscribe' and token == self.verify_token:
            logger.info("Webhook de WhatsApp verificado exitosamente")
            return challenge
        else:
            logger.warning("Verificación de webhook fallida")
            return None
    
    def process_webhook(self, webhook_data: Dict) -> bool:
        """
        Procesa los webhooks entrantes de WhatsApp
        
        Args:
            webhook_data: Datos del webhook
            
        Returns:
            bool: True si se procesó exitosamente
        """
        try:
            if webhook_data.get('object') != 'whatsapp_business_account':
                return False
            
            for entry in webhook_data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('value', {}).get('statuses'):
                        for status in change['value']['statuses']:
                            self._update_message_status(status)
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return False
    
    def _update_message_status(self, status_data: Dict):
        """
        Actualiza el estado de un mensaje basado en el webhook
        
        Args:
            status_data: Datos del estado del mensaje
        """
        try:
            message_id = status_data.get('id')
            status = status_data.get('status')
            
            if not message_id or not status:
                return
            
            # Buscar mensaje por WhatsApp message ID
            message = WhatsAppMessage.objects.filter(
                whatsapp_message_id=message_id
            ).first()
            
            if not message:
                logger.warning(f"Mensaje no encontrado para ID: {message_id}")
                return
            
            # Actualizar estado
            if status == 'sent':
                message.mark_as_sent(message_id)
            elif status == 'delivered':
                message.mark_as_delivered()
            elif status == 'read':
                message.mark_as_read()
            
            logger.info(f"Estado del mensaje {message.id} actualizado a: {status}")
            
        except Exception as e:
            logger.error(f"Error actualizando estado del mensaje: {str(e)}")


# Instancia global del servicio
whatsapp_service = WhatsAppService() 