#!/usr/bin/env python
"""
Configuración de prueba para el endpoint /test/hola-jon
Este archivo contiene configuraciones específicas para testing
"""

# Configuración de prueba para WhatsApp
TEST_CONFIG = {
    'test_phone_number': '5552967027',
    'test_message': '¡Hola Jon! Este es un mensaje de prueba del servicio de WhatsApp.',
    'test_order_id': 'TEST_HOLA_JON',
    'endpoint_url': '/api/whatsapp/test/hola-jon/',
    'expected_response': {
        'success': True,
        'message': 'Mensaje de prueba enviado exitosamente',
        'data': {
            'phone_number': '5552967027',
            'message_content': '¡Hola Jon! Este es un mensaje de prueba del servicio de WhatsApp.',
            'message_id': 'N/A'  # Se actualiza cuando se envía realmente
        }
    }
}

# Configuración de variables de entorno para testing
TEST_ENV_VARS = {
    'WHATSAPP_API_URL': 'https://graph.facebook.com/v18.0',
    'WHATSAPP_PHONE_NUMBER_ID': '123456789012345',  # ID de prueba
    'WHATSAPP_ACCESS_TOKEN': 'EAABwzLixnjYBO...',  # Token de prueba
    'WHATSAPP_VERIFY_TOKEN': 'enid-store-whatsapp-verify-token-2024',
    'DEBUG': 'True',
    'SECRET_KEY': 'django-insecure-whatsapp-test-key',
}

# Instrucciones de prueba
TEST_INSTRUCTIONS = """
INSTRUCCIONES PARA PROBAR EL ENDPOINT /test/hola-jon:

1. Asegúrate de que el servicio esté corriendo:
   docker-compose up --build

2. Verifica que las variables de entorno estén configuradas en .env:
   - WHATSAPP_PHONE_NUMBER_ID
   - WHATSAPP_ACCESS_TOKEN
   - WHATSAPP_VERIFY_TOKEN

3. Ejecuta las migraciones si es necesario:
   docker-compose exec web python manage.py migrate

4. Prueba el endpoint:
   curl -X GET http://localhost:8001/api/whatsapp/test/hola-jon/

5. Verifica la respuesta:
   - Debe retornar status 200
   - success: true
   - message: "Mensaje de prueba enviado exitosamente"
   - data.phone_number: "5552967027"

6. Verifica en los logs que el mensaje se haya enviado:
   docker-compose logs web

NOTA: Este endpoint envía un mensaje real de WhatsApp al número 5552967027.
Asegúrate de que el número esté configurado correctamente en tu cuenta de WhatsApp Business.
"""

if __name__ == "__main__":
    print("Configuración de prueba para endpoint /test/hola-jon")
    print("=" * 60)
    print(TEST_INSTRUCTIONS) 