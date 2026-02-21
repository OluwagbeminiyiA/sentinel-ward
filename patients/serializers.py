from rest_framework import serializers
from .models import Patient
from bed_node.models import LatestVitals


class PatientListSerializer(serializers.ModelSerializer):
    """Serializer for Patient list view with vitals info"""
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    
    # Vitals information (nested from LatestVitals)
    temperature = serializers.SerializerMethodField()
    heart_rate = serializers.SerializerMethodField()
    spo2 = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    trend = serializers.SerializerMethodField()
    vitals_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'name', 'bed_number', 'ward',
            'hospital', 'hospital_name', 'created_at',
            'temperature', 'heart_rate', 'spo2',
            'risk_level', 'trend', 'vitals_updated_at'
        ]
    
    def get_temperature(self, obj):
        """Get latest temperature"""
        try:
            return str(obj.latest_vitals.temperature) if obj.latest_vitals.temperature else None
        except LatestVitals.DoesNotExist:
            return None
    
    def get_heart_rate(self, obj):
        """Get latest heart rate"""
        try:
            return obj.latest_vitals.heart_rate
        except LatestVitals.DoesNotExist:
            return None
    
    def get_spo2(self, obj):
        """Get latest SpO2"""
        try:
            return obj.latest_vitals.spo2
        except LatestVitals.DoesNotExist:
            return None
    
    def get_risk_level(self, obj):
        """Get risk level"""
        try:
            return obj.latest_vitals.risk_level
        except LatestVitals.DoesNotExist:
            return ''
    
    def get_trend(self, obj):
        """Get vitals trend"""
        try:
            return obj.latest_vitals.trend
        except LatestVitals.DoesNotExist:
            return ''
    
    def get_vitals_updated_at(self, obj):
        """Get vitals last update timestamp"""
        try:
            return obj.latest_vitals.updated_at
        except LatestVitals.DoesNotExist:
            return None


class PatientDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single patient view"""
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'name', 'bed_number', 'ward',
            'hospital', 'hospital_name', 'past_medical_records', 'created_at'
        ]
