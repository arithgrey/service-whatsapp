"""
URLs para la aplicación de notificaciones
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Endpoints para notificaciones
    path('send/', views.SendNotificationView.as_view(), name='send_notification'),
    path('batch/', views.SendBatchNotificationView.as_view(), name='send_batch_notification'),
    path('schedule/', views.ScheduleNotificationView.as_view(), name='schedule_notification'),
    
    # Endpoints para gestión de notificaciones
    path('list/', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/cancel/', views.CancelNotificationView.as_view(), name='cancel_notification'),
    
    # Endpoints para configuración
    path('settings/', views.NotificationSettingsView.as_view(), name='notification_settings'),
    path('templates/', views.NotificationTemplateListView.as_view(), name='template_list'),
] 