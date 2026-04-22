from django.contrib import admin
from .models import Complaint, ComplaintAttachment


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'landlord', 'title', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'tenant__name', 'landlord__username')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'responded_at')
    fieldsets = (
        ('Complaint Details', {
            'fields': ('tenant', 'landlord', 'title', 'description', 'priority', 'status')
        }),
        ('Response', {
            'fields': ('landlord_response', 'responded_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ComplaintAttachment)
class ComplaintAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('complaint__title',)
    readonly_fields = ('uploaded_at',)
