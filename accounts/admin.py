from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'hospital', 'created_at']
    list_filter = ['hospital', 'created_at']
    search_fields = ['full_name', 'user__username', 'user__email', 'hospital__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'hospital')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
