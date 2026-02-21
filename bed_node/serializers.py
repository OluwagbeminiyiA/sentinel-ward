from rest_framework import serializers
from .models import Device, LatestVitals, Prediction, Alert
from patients.models import Patient


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model"""
    
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'bed_number', 'status', 'last_seen']
        read_only_fields = ['last_seen']


class LatestVitalsSerializer(serializers.ModelSerializer):
    """Serializer for LatestVitals model"""
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    
    class Meta:
        model = LatestVitals
        fields = [
            'patient', 'patient_id', 'patient_name',
            'temperature', 'heart_rate', 'spo2',
            'risk_level', 'ai_analysis', 'updated_at'
        ]
        read_only_fields = ['updated_at', 'ai_analysis']


class VitalsDataSerializer(serializers.Serializer):
    """Serializer for incoming vitals data from IoT devices"""
    device_id = serializers.CharField(max_length=100)
    patient_id = serializers.CharField(max_length=50)
    temperature = serializers.DecimalField(max_digits=4, decimal_places=1, required=False, allow_null=True)
    heart_rate = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=300)
    spo2 = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    timestamp = serializers.DateTimeField(required=False)


class PredictionSerializer(serializers.ModelSerializer):
    """Serializer for Prediction model"""
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    
    class Meta:
        model = Prediction
        fields = [
            'id', 'patient', 'patient_id', 'patient_name',
            'risk_level', 'confidence', 'drivers', 'created_at'
        ]
        read_only_fields = ['created_at']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model"""
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    bed_number = serializers.CharField(source='patient.bed_number', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'patient', 'patient_id', 'patient_name', 'bed_number',
            'type', 'message', 'severity', 'ai_analysis', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']
