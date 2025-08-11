"""
Admin para la aplicación de notificaciones
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import NotificationTemplate, Notification, NotificationSettings


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin para plantillas de notificaciones"""
    
    list_display = [
        'name', 
        'notification_type', 
        'is_active', 
        'created_at', 
        'created_by'
    ]
    
    list_filter = [
        'notification_type', 
        'is_active', 
        'created_at'
    ]
    
    search_fields = ['name', 'title', 'content']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('Contenido', {
            'fields': ('title', 'content')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva plantilla
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin para notificaciones"""
    
    list_display = [
        'recipient', 
        'channel', 
        'notification_type', 
        'status', 
        'created_at',
        'sent_at'
    ]
    
    list_filter = [
        'channel', 
        'status', 
        'notification_type', 
        'created_at',
        'sent_at'
    ]
    
    search_fields = ['recipient', 'title', 'content']
    
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'sent_at', 
        'delivered_at'
    ]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('recipient', 'channel', 'notification_type', 'status')
        }),
        ('Contenido', {
            'fields': ('title', 'content', 'template')
        }),
        ('Programación', {
            'fields': ('scheduled_at',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('metadata', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_sent', 'mark_as_failed', 'cancel_notifications']
    
    def mark_as_sent(self, request, queryset):
        """Marca las notificaciones seleccionadas como enviadas"""
        updated = queryset.update(status='sent')
        self.message_user(
            request, 
            f'{updated} notificación(es) marcada(s) como enviada(s)'
        )
    mark_as_sent.short_description = "Marcar como enviadas"
    
    def mark_as_failed(self, request, queryset):
        """Marca las notificaciones seleccionadas como fallidas"""
        updated = queryset.update(status='failed')
        self.message_user(
            request, 
            f'{updated} notificación(es) marcada(s) como fallida(s)'
        )
    mark_as_failed.short_description = "Marcar como fallidas"
    
    def cancel_notifications(self, request, queryset):
        """Cancela las notificaciones pendientes seleccionadas"""
        pending = queryset.filter(status='pending')
        updated = pending.update(status='cancelled')
        self.message_user(
            request, 
            f'{updated} notificación(es) cancelada(s)'
        )
    cancel_notifications.short_description = "Cancelar notificaciones pendientes"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'created_by')


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Admin para configuraciones de notificaciones"""
    
    list_display = [
        'user', 
        'whatsapp_enabled', 
        'email_enabled', 
        'sms_enabled', 
        'push_enabled',
        'timezone'
    ]
    
    list_filter = [
        'whatsapp_enabled', 
        'email_enabled', 
        'sms_enabled', 
        'push_enabled',
        'timezone'
    ]
    
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Canales habilitados', {
            'fields': ('whatsapp_enabled', 'email_enabled', 'sms_enabled', 'push_enabled')
        }),
        ('Configuración de tiempo', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'timezone'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user') 