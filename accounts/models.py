from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Hospital staff profile"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Associated Django user'
    )
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='staff',
        help_text='Associated hospital'
    )
    full_name = models.CharField(
        max_length=255,
        help_text='Full name of the user'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Account creation timestamp'
    )
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.hospital.name}"
