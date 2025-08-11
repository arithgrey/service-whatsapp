# WhatsApp Notification Service - Enid Store

Servicio microservicio para manejar notificaciones automáticas de WhatsApp para la plataforma Enid Store.

## 🚀 Características

- **Notificaciones automáticas** para pedidos y actualizaciones de estado
- **Plantillas personalizables** para diferentes tipos de mensajes
- **Integración con WhatsApp Business API** para envío de mensajes
- **Webhooks** para recibir actualizaciones de estado de mensajes
- **API REST completa** para gestión de plantillas y mensajes
- **Soporte multiidioma** (Español e Inglés)
- **Logging detallado** para monitoreo y debugging
- **Docker** para fácil despliegue

## 🏗️ Arquitectura

```
service-whatsapp/
├── app/                    # Configuración principal de Django
├── whatsapp/              # Aplicación principal de WhatsApp
│   ├── models.py          # Modelos de base de datos
│   ├── serializers.py     # Serializers para API
│   ├── services.py        # Lógica de negocio
│   ├── views.py           # Vistas de API
│   └── urls.py            # Rutas de URL
├── notifications/          # Aplicación de gestión de notificaciones
├── templates/              # Plantillas de mensajes
└── docker-compose.yml      # Configuración de Docker
```

## 📋 Requisitos

- Python 3.11+
- Django 4.2.7
- PostgreSQL 15+
- WhatsApp Business API (configuración)

## 🛠️ Instalación

### 1. Clonar y configurar

```bash
cd service-whatsapp
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Usando Docker (Recomendado)

```bash
# Construir y ejecutar
docker-compose up --build

# En otra terminal, ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Inicializar plantillas básicas
docker-compose exec web python manage.py shell < initial_whatsapp_templates.py
```

### 3. Instalación local

```bash
# Crear entorno virtual
python -m venv env
source env/bin/activate  # Linux/Mac
# o
env\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate

# Ejecutar servidor
python manage.py runserver
```

## ⚙️ Configuración

### Variables de entorno (.env)

```bash
# Django
SECRET_KEY=tu-clave-secreta
DEBUG=True

# Base de datos
DB_NAME=whatsapp_service
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# WhatsApp Business API
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_PHONE_NUMBER_ID=tu-phone-number-id
WHATSAPP_ACCESS_TOKEN=tu-access-token
WHATSAPP_VERIFY_TOKEN=tu-verify-token

# Enid Store Service
ENID_STORE_URL=http://localhost:8000
ENID_STORE_API_KEY=tu-api-key
```

### Configuración de WhatsApp Business API

1. Crear cuenta en [Meta for Developers](https://developers.facebook.com/)
2. Crear aplicación y configurar WhatsApp Business API
3. Obtener Phone Number ID y Access Token
4. Configurar webhook con URL: `https://tu-dominio.com/api/whatsapp/webhook/`

## 📱 API Endpoints

### WhatsApp

#### Envío de mensajes
- `POST /api/whatsapp/send/text/` - Enviar mensaje de texto
- `POST /api/whatsapp/send/template/` - Enviar mensaje con plantilla
- `POST /api/whatsapp/send/order-confirmation/` - Confirmación de pedido
- `POST /api/whatsapp/send/order-status-update/` - Actualización de estado

#### Gestión de plantillas
- `GET /api/whatsapp/templates/` - Listar plantillas
- `POST /api/whatsapp/templates/create/` - Crear plantilla
- `GET /api/whatsapp/templates/{id}/` - Detalle de plantilla
- `PUT /api/whatsapp/templates/{id}/update/` - Actualizar plantilla
- `DELETE /api/whatsapp/templates/{id}/delete/` - Eliminar plantilla

#### Gestión de mensajes
- `GET /api/whatsapp/messages/` - Listar mensajes
- `GET /api/whatsapp/messages/{id}/` - Detalle de mensaje
- `POST /api/whatsapp/messages/{id}/resend/` - Reenviar mensaje

#### Webhooks
- `GET /api/whatsapp/webhook/` - Verificación de webhook
- `POST /api/whatsapp/webhook/` - Recibir webhooks

#### Utilidades
- `GET /api/whatsapp/status/` - Estado del servicio
- `GET /api/whatsapp/stats/` - Estadísticas de mensajes

### Notificaciones

- `POST /api/notifications/send/` - Enviar notificación individual
- `POST /api/notifications/batch/` - Enviar notificaciones en lote
- `GET /api/notifications/settings/` - Configuración del servicio

## 🔧 Uso

### Enviar confirmación de pedido

```python
import requests

url = "http://localhost:8001/api/whatsapp/send/order-confirmation/"
data = {
    "phone_number": "+1234567890",
    "order_data": {
        "id": "ORD-001",
        "total": 99.99,
        "created_at": "2024-01-15T10:30:00Z",
        "shipping_address": {
            "street": "Calle Principal 123",
            "city": "Ciudad",
            "state": "Estado"
        }
    },
    "customer_name": "Juan Pérez"
}

response = requests.post(url, json=data, headers={
    "Authorization": "Bearer tu-token-jwt"
})
```

### Enviar mensaje con plantilla

```python
url = "http://localhost:8001/api/whatsapp/send/template/"
data = {
    "phone_number": "+1234567890",
    "template_name": "order_status_update",
    "variables": {
        "order_id": "ORD-001",
        "status": "En preparación",
        "update_time": "15/01/2024 10:30",
        "additional_info": "Tu pedido está siendo empacado"
    }
}

response = requests.post(url, json=data, headers={
    "Authorization": "Bearer tu-token-jwt"
})
```

## 📊 Plantillas disponibles

### Español
- `order_confirmation` - Confirmación de pedido
- `order_status_update` - Actualización de estado
- `order_delivered` - Pedido entregado
- `order_cancelled` - Pedido cancelado
- `payment_confirmed` - Pago confirmado
- `shipping_update` - Actualización de envío
- `welcome_message` - Mensaje de bienvenida

### Inglés
- `order_confirmation_en` - Order confirmation
- `order_status_update_en` - Order status update

## 🔗 Integración con Enid Store

Para integrar este servicio con el servicio principal de Enid Store:

1. **Configurar webhook** en el servicio de pedidos
2. **Llamar API** cuando se cree/actualice un pedido
3. **Manejar respuestas** y errores apropiadamente

### Ejemplo de integración

```python
# En enid-store/order/views.py
from django.conf import settings
import requests

def send_whatsapp_notification(order, customer):
    """Envía notificación WhatsApp cuando se crea un pedido"""
    try:
        url = f"{settings.WHATSAPP_SERVICE_URL}/api/whatsapp/send/order-confirmation/"
        
        data = {
            "phone_number": customer.phone_number,
            "order_data": {
                "id": order.id,
                "total": float(order.total),
                "created_at": order.created_at.isoformat(),
                "shipping_address": order.shipping_address.to_dict()
            },
            "customer_name": customer.full_name
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Notificación WhatsApp enviada para pedido {order.id}")
        else:
            logger.error(f"Error enviando notificación WhatsApp: {response.text}")
            
    except Exception as e:
        logger.error(f"Error enviando notificación WhatsApp: {str(e)}")
```

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Tests específicos
python manage.py test whatsapp.tests
python manage.py test notifications.tests
```

## 📝 Logs

Los logs se guardan en:
- Consola (stdout)
- Archivo: `logs/whatsapp_service.log`

### Niveles de log
- `INFO` - Operaciones normales
- `WARNING` - Advertencias
- `ERROR` - Errores
- `DEBUG` - Información de debugging (solo en desarrollo)

## 🚀 Despliegue

### Producción

1. **Configurar variables de entorno** para producción
2. **Usar Gunicorn** en lugar del servidor de desarrollo
3. **Configurar Nginx** como proxy reverso
4. **Configurar SSL/TLS** para webhooks
5. **Monitorear logs** y métricas

### Docker Compose para producción

```yaml
version: '3.8'
services:
  web:
    build: .
    command: gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 4
    environment:
      - DEBUG=False
      - DJANGO_SETTINGS_MODULE=app.settings
    restart: unless-stopped
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico:
- Crear issue en el repositorio
- Contactar al equipo de desarrollo
- Revisar documentación de la API

## 🔮 Roadmap

- [ ] **Notificaciones programadas** con Celery
- [ ] **Múltiples canales** (SMS, Email, Push)
- [ ] **Dashboard de analytics** para métricas
- [ ] **Plantillas dinámicas** con editor visual
- [ ] **Integración con CRM** para seguimiento de clientes
- [ ] **API GraphQL** para consultas complejas
- [ ] **Webhooks personalizables** para eventos específicos
- [ ] **Sistema de retry** para mensajes fallidos
- [ ] **Rate limiting** para prevenir spam
- [ ] **Métricas en tiempo real** con WebSockets

---

**Desarrollado con ❤️ para Enid Store** 