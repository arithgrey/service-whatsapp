from django.contrib import admin
from .models import WhatsAppMessage, WhatsAppTemplate

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone_number', 'message_type', 'status', 'created_at']
    list_filter = ['status', 'message_type', 'created_at']
    search_fields = ['phone_number', 'message_content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'language', 'is_active']
    search_fields = ['name', 'content']
    readonly_fields = ['created_at', 'updated_at'] 