from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'name', 'bed_number', 'ward', 'hospital', 'created_at']
    list_filter = ['hospital', 'ward', 'created_at']
    search_fields = ['patient_id', 'name', 'bed_number', 'ward']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'name', 'bed_number', 'ward', 'hospital')
        }),
        ('Medical History', {
            'fields': ('past_medical_records',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
