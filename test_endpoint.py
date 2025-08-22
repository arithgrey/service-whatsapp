#!/usr/bin/env python
"""
Script de prueba para el endpoint /test/hola-jon
Ejecutar con: python test_endpoint.py
"""

import requests
import json
import time
from datetime import datetime

def test_hola_jon_endpoint():
    """Prueba el endpoint /test/hola-jon"""
    
    # Configuración de la prueba
    base_url = "http://localhost:8001"
    endpoint = "/api/whatsapp/test/hola-jon/"
    full_url = base_url + endpoint
    
    print("🧪 PRUEBA DEL ENDPOINT /test/hola-jon")
    print("=" * 60)
    print(f"URL: {full_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Realizar la petición GET
        print("📤 Enviando petición GET...")
        response = requests.get(full_url, timeout=30)
        
        print(f"📥 Respuesta recibida:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print()
        
        # Procesar la respuesta
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ RESPUESTA EXITOSA:")
                print(f"   Success: {data.get('success', 'N/A')}")
                print(f"   Message: {data.get('message', 'N/A')}")
                
                if 'data' in data:
                    print("   📱 Datos del mensaje:")
                    print(f"      Phone Number: {data['data'].get('phone_number', 'N/A')}")
                    print(f"      Message Content: {data['data'].get('message_content', 'N/A')}")
                    print(f"      Message ID: {data['data'].get('message_id', 'N/A')}")
                
                # Verificar que la respuesta sea la esperada
                expected_phone = "5552967027"
                actual_phone = data.get('data', {}).get('phone_number', '')
                
                if actual_phone == expected_phone:
                    print(f"   ✅ Número de teléfono correcto: {actual_phone}")
                else:
                    print(f"   ❌ Número de teléfono incorrecto. Esperado: {expected_phone}, Recibido: {actual_phone}")
                
                if data.get('success') == True:
                    print("   ✅ Campo 'success' es True")
                else:
                    print("   ❌ Campo 'success' no es True")
                
            except json.JSONDecodeError:
                print("❌ ERROR: La respuesta no es JSON válido")
                print(f"   Contenido: {response.text}")
                
        elif response.status_code == 404:
            print("❌ ERROR: Endpoint no encontrado (404)")
            print("   Verifica que el servicio esté corriendo y la URL sea correcta")
            
        elif response.status_code == 500:
            print("❌ ERROR: Error interno del servidor (500)")
            print("   Verifica los logs del servicio para más detalles")
            
        else:
            print(f"❌ ERROR: Status code inesperado: {response.status_code}")
            print(f"   Contenido: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servicio")
        print("   Verifica que el servicio esté corriendo en http://localhost:8001")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout en la petición")
        print("   El servicio tardó demasiado en responder")
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {str(e)}")
    
    print()
    print("=" * 60)
    print("🏁 Prueba completada")

def test_swagger_documentation():
    """Prueba que la documentación Swagger esté disponible"""
    
    base_url = "http://localhost:8001"
    swagger_url = base_url + "/swagger/"
    
    print("📚 PRUEBA DE DOCUMENTACIÓN SWAGGER")
    print("=" * 60)
    print(f"URL: {swagger_url}")
    print()
    
    try:
        response = requests.get(swagger_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Swagger UI disponible")
            print("   La documentación de la API está accesible")
        else:
            print(f"❌ Swagger UI no disponible. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accediendo a Swagger: {str(e)}")
    
    print()

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL SERVICIO WHATSAPP")
    print()
    
    # Probar Swagger primero
    test_swagger_documentation()
    
    # Probar el endpoint principal
    test_hola_jon_endpoint()
    
    print()
    print("💡 CONSEJOS:")
    print("   - Si hay errores de conexión, ejecuta: docker-compose up --build")
    print("   - Si hay errores 500, verifica las variables de entorno en .env")
    print("   - Si hay errores 404, verifica que las URLs estén correctas")
    print("   - Para ver logs: docker-compose logs web") 