from django.db import models
from hospitals.models import Hospital


class Patient(models.Model):
    """Patient entity for hospital monitoring"""
    patient_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Human-readable patient ID (e.g., PAT_0045)'
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Patient name (optional for demo)'
    )
    bed_number = models.CharField(
        max_length=50,
        help_text='Bed number assigned to patient'
    )
    ward = models.CharField(
        max_length=100,
        help_text='Ward where patient is located'
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='patients',
        help_text='Hospital where patient is admitted'
    )
    past_medical_records = models.TextField(
        blank=True,
        null=True,
        help_text='Past medical history and records'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Patient admission timestamp'
    )
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
        unique_together = [['bed_number', 'hospital']]
    
    def __str__(self):
        name_display = self.name if self.name else 'Demo Patient'
        return f"{self.patient_id} - {name_display} (Bed {self.bed_number})"
