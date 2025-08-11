"""
URLs principales del servicio de notificaciones WhatsApp
Siguiendo las reglas del backend: Swagger obligatorio para todas las APIs
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Configuración de Swagger obligatoria
schema_view = get_schema_view(
    openapi.Info(
        title="WhatsApp Notification Service API",
        default_version='v1',
        description="API para envío de notificaciones automáticas de pedidos a través de WhatsApp",
        terms_of_service="https://www.ejemplo.com/terms/",
        contact=openapi.Contact(email="dev@ejemplo.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/whatsapp/', include('whatsapp.urls')),
    path('api/notifications/', include('notifications.urls')),
    
    # URLs de Swagger obligatorias
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 