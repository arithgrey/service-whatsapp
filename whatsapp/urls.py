"""
URLs para la aplicación de WhatsApp
"""

from django.urls import path
from . import views

app_name = 'whatsapp'

urlpatterns = [
    # Endpoints para envío de mensajes
    path('send/text/', views.SendTextMessageView.as_view(), name='send_text_message'),
    path('send/template/', views.SendTemplateMessageView.as_view(), name='send_template_message'),
    path('send/order-confirmation/', views.SendOrderConfirmationView.as_view(), name='send_order_confirmation'),
    path('send/order-status-update/', views.SendOrderStatusUpdateView.as_view(), name='send_order_status_update'),
    
    # Endpoints para plantillas
    path('templates/', views.WhatsAppTemplateListView.as_view(), name='template_list'),
    path('templates/<int:pk>/', views.WhatsAppTemplateDetailView.as_view(), name='template_detail'),
    path('templates/create/', views.WhatsAppTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/update/', views.WhatsAppTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.WhatsAppTemplateDeleteView.as_view(), name='template_delete'),
    
    # Endpoints para mensajes
    path('messages/', views.WhatsAppMessageListView.as_view(), name='message_list'),
    path('messages/<int:pk>/', views.WhatsAppMessageDetailView.as_view(), name='message_detail'),
    path('messages/<int:pk>/resend/', views.ResendMessageView.as_view(), name='resend_message'),
    
    # Webhooks de WhatsApp
    path('webhook/', views.WhatsAppWebhookView.as_view(), name='webhook'),
    
    # Endpoints de utilidad
    path('status/', views.ServiceStatusView.as_view(), name='service_status'),
    path('stats/', views.MessageStatsView.as_view(), name='message_stats'),
    
    # Circuit Breaker (obligatorio según reglas del backend)
    path('circuit-breaker/status/', views.circuit_breaker_status, name='circuit_breaker_status'),

    # Nuevas URLs para notificaciones de pedidos
    path('order-notification/', views.SendOrderNotificationView.as_view(), name='send_order_notification'),
    path('bulk-order-notifications/', views.SendBulkOrderNotificationsView.as_view(), name='send_bulk_order_notifications'),
    
    # Endpoint de prueba para WhatsApp
    path('test/hola-jon/', views.TestHolaJonView.as_view(), name='test_hola_jon'),
] 