from django.db import models
from patients.models import Patient


class Device(models.Model):
    """IoT hardware units for patient monitoring"""
    
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    ]
    
    device_id = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique device identifier (e.g., bed_12_node)'
    )
    bed_number = models.CharField(
        max_length=50,
        help_text='Associated bed number'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='OFFLINE',
        help_text='Current device status'
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        help_text='Last time the device was active'
    )
    
    class Meta:
        ordering = ['bed_number', 'device_id']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
    
    def __str__(self):
        return f"{self.device_id} (Bed {self.bed_number}) - {self.status}"


class LatestVitals(models.Model):
    """Current vital signs state per patient - powers the dashboard"""
    
    TREND_CHOICES = [
        ('STABLE', 'Stable'),
        ('RISING', 'Rising'),
        ('FALLING', 'Falling'),
    ]
    
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='latest_vitals',
        help_text='Patient for these vital signs'
    )
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Body temperature in Celsius'
    )
    heart_rate = models.IntegerField(
        null=True,
        blank=True,
        help_text='Heart rate in BPM'
    )
    spo2 = models.IntegerField(
        null=True,
        blank=True,
        help_text='Blood oxygen saturation percentage'
    )
    risk_level = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Calculated risk level (e.g., LOW, MEDIUM, HIGH)'
    )
    trend = models.CharField(
        max_length=10,
        choices=TREND_CHOICES,
        default='STABLE',
        help_text='Vital signs trend'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        verbose_name = 'Latest Vitals'
        verbose_name_plural = 'Latest Vitals'
        ordering = ['-updated_at']
    
    def __str__(self):
        patient_name = self.patient.name or f"Patient {self.patient.patient_id}"
        return f"{patient_name} - {self.trend} ({self.updated_at.strftime('%Y-%m-%d %H:%M')})"


class Prediction(models.Model):
    """AI risk engine predictions for patients"""
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='predictions',
        help_text='Patient this prediction is for'
    )
    risk_level = models.CharField(
        max_length=20,
        help_text='Predicted risk level (e.g., LOW, MEDIUM, HIGH, CRITICAL)'
    )
    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Confidence score (0.00 to 100.00)'
    )
    drivers = models.TextField(
        blank=True,
        default='',
        help_text='JSON or text describing risk factors and drivers'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this prediction was created'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prediction'
        verbose_name_plural = 'Predictions'
        indexes = [
            models.Index(fields=['patient', '-created_at']),
            models.Index(fields=['risk_level']),
        ]
    
    def __str__(self):
        patient_name = self.patient.name or f"Patient {self.patient.patient_id}"
        return f"{patient_name} - {self.risk_level} ({self.confidence}% confidence)"


class Alert(models.Model):
    """Clinical alerts for patient monitoring - high visibility for critical events"""
    
    TYPE_CHOICES = [
        ('HIGH_RISK', 'High Risk'),
        ('WARNING', 'Warning'),
        ('DEVICE_OFFLINE', 'Device Offline'),
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='alerts',
        help_text='Patient this alert is for'
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text='Alert type/category'
    )
    message = models.TextField(
        help_text='Alert message/description'
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        help_text='Alert severity level'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the alert is still active'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this alert was created'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        indexes = [
            models.Index(fields=['patient', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['type', 'severity']),
        ]
    
    def __str__(self):
        patient_name = self.patient.name or f"Patient {self.patient.patient_id}"
        status = "ACTIVE" if self.is_active else "RESOLVED"
        return f"[{status}] {self.type} - {patient_name} ({self.severity})"


