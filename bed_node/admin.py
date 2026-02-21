from django.contrib import admin
from .models import Device, LatestVitals, Prediction, Alert


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'bed_number', 'status', 'last_seen']
    list_filter = ['status', 'last_seen']
    search_fields = ['device_id', 'bed_number']
    readonly_fields = ['last_seen']
    
    fieldsets = [
        ('Device Information', {
            'fields': ['device_id', 'bed_number']
        }),
        ('Status', {
            'fields': ['status', 'last_seen']
        }),
    ]


@admin.register(LatestVitals)
class LatestVitalsAdmin(admin.ModelAdmin):
    list_display = ['patient', 'temperature', 'heart_rate', 'spo2', 'risk_level', 'updated_at']  # 'trend' removed
    list_filter = ['risk_level', 'updated_at']  # 'trend' removed
    search_fields = ['patient__patient_id', 'patient__name']
    readonly_fields = ['updated_at', 'ai_analysis']
    
    fieldsets = [
        ('Patient', {
            'fields': ['patient']
        }),
        ('Vital Signs', {
            'fields': ['temperature', 'heart_rate', 'spo2']
        }),
        ('Analysis', {
            'fields': ['risk_level', 'ai_analysis', 'updated_at']  # 'trend' removed, 'ai_analysis' added
        }),
    ]


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'risk_level', 'confidence', 'created_at']
    list_filter = ['risk_level', 'created_at']
    search_fields = ['patient__patient_id', 'patient__name', 'risk_level']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Patient', {
            'fields': ['patient']
        }),
        ('Risk Assessment', {
            'fields': ['risk_level', 'confidence']
        }),
        ('Analysis Details', {
            'fields': ['drivers', 'created_at']
        }),
    ]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['patient', 'type', 'severity', 'is_active', 'created_at']
    list_filter = ['type', 'severity', 'is_active', 'created_at']
    search_fields = ['patient__patient_id', 'patient__name', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_active']
    
    fieldsets = [
        ('Patient', {
            'fields': ['patient']
        }),
        ('Alert Details', {
            'fields': ['type', 'severity', 'message', 'ai_analysis']
        }),
        ('Status', {
            'fields': ['is_active', 'created_at']
        }),
    ]
    
    def get_list_display_links(self, request, list_display):
        """Make patient the only clickable link"""
        return ['patient']


