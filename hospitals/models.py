from django.db import models


class Hospital(models.Model):
    """Hospital entity"""
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Hospital name'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Registration timestamp'
    )
    
    class Meta:
        db_table = 'hospitals'
        ordering = ['name']
    
    def __str__(self):
        return self.name
