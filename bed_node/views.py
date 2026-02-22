from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal
import random
import logging

from .models import Device, LatestVitals, Prediction, Alert
from .serializers import (
    DeviceSerializer, LatestVitalsSerializer, VitalsDataSerializer,
    PredictionSerializer, AlertSerializer
)
from patients.models import Patient
from patients.serializers import PatientListSerializer
from .ai_service import get_analyzer

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_description='Receive vital signs data from IoT device and update patient vitals',
    request_body=VitalsDataSerializer,
    responses={
        200: openapi.Response('Vitals updated successfully', LatestVitalsSerializer),
        400: 'Bad request - validation error',
        404: 'Patient or device not found'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # IoT devices don't use JWT auth
def receive_vitals(request):
    """
    Receive vital signs data from IoT device.
    Updates LatestVitals and Device status.
    Generates alerts if vitals are critical.
    """
    serializer = VitalsDataSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    device_id = data.get('device_id')
    patient_id = data.get('patient_id')
    
    # Verify device exists
    try:
        device = Device.objects.get(device_id=device_id)
        device.status = 'ONLINE'
        device.save()
    except Device.DoesNotExist:
        return Response(
            {'error': f'Device {device_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify patient exists
    try:
        patient = Patient.objects.get(patient_id=patient_id)
    except Patient.DoesNotExist:
        return Response(
            {'error': f'Patient {patient_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Update or create latest vitals
    vitals, created = LatestVitals.objects.update_or_create(
        patient=patient,
        defaults={
            'temperature': data.get('temperature'),
            'heart_rate': data.get('heart_rate'),
            'spo2': data.get('spo2'),
        }
    )
    
    # Calculate risk level based on vitals
    risk_level, alerts_to_create = _assess_risk(patient, vitals)
    vitals.risk_level = risk_level
    
    # Trend detection commented out - requires historical vitals tracking
    # vitals.trend = _calculate_trend(vitals)
    
    # Generate AI analysis using Gemini
    try:
        analyzer = get_analyzer()
        ai_analysis = analyzer.analyze_vitals(patient, vitals)
        vitals.ai_analysis = ai_analysis
        logger.info(f"AI analysis generated for patient {patient_id}")
    except Exception as e:
        logger.error(f"AI analysis failed for patient {patient_id}: {str(e)}")
        vitals.ai_analysis = "AI analysis unavailable"
    
    vitals.save()
    
    # Create alerts if needed
    for alert_data in alerts_to_create:
        Alert.objects.create(
            patient=patient,
            type=alert_data['type'],
            message=alert_data['message'],
            severity=alert_data['severity']
        )
    
    return Response({
        'status': 'success',
        'message': 'Vitals updated successfully',
        'vitals': LatestVitalsSerializer(vitals).data
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description='Simulate IoT device sending vital signs data (for testing)',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'device_id': openapi.Schema(type=openapi.TYPE_STRING, description='Device ID'),
            'patient_id': openapi.Schema(type=openapi.TYPE_STRING, description='Patient ID'),
        },
        required=['device_id', 'patient_id']
    ),
    responses={
        200: 'Simulated vitals sent successfully',
        404: 'Patient or device not found'
    }
)
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])  # Allow unauthenticated access for simulation and demo
def simulate_vitals(request):
    """
    Simulate vital signs data from an IoT device.
    Generates random but realistic vital signs.
    """
    device_id = request.data.get('device_id')
    patient_id = request.data.get('patient_id')
    
    if not device_id or not patient_id:
        return Response(
            {'error': 'device_id and patient_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate realistic simulated vitals
    simulated_data = {
        'device_id': device_id,
        'patient_id': patient_id,
        'temperature': round(random.uniform(36.0, 39.5), 1),
        'heart_rate': random.randint(50, 150),
        'spo2': random.randint(85, 100)
    }
    
    # Process the simulated data (same logic as receive_vitals)
    serializer = VitalsDataSerializer(data=simulated_data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Verify device exists
    try:
        device = Device.objects.get(device_id=device_id)
        device.status = 'ONLINE'
        device.save()
    except Device.DoesNotExist:
        return Response(
            {'error': f'Device {device_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify patient exists
    try:
        patient = Patient.objects.get(patient_id=patient_id)
    except Patient.DoesNotExist:
        return Response(
            {'error': f'Patient {patient_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Update or create latest vitals
    vitals, created = LatestVitals.objects.update_or_create(
        patient=patient,
        defaults={
            'temperature': data.get('temperature'),
            'heart_rate': data.get('heart_rate'),
            'spo2': data.get('spo2'),
        }
    )
    
    # Calculate risk level based on vitals
    risk_level, alerts_to_create = _assess_risk(patient, vitals)
    vitals.risk_level = risk_level
    # Trend detection commented out - requires historical vitals tracking
    # vitals.trend = _calculate_trend(vitals)
    
    # Generate AI analysis using Gemini
    try:
        analyzer = get_analyzer()
        ai_analysis = analyzer.analyze_vitals(patient, vitals)
        vitals.ai_analysis = ai_analysis
        logger.info(f"AI analysis generated for simulated vitals - patient {patient_id}")
    except Exception as e:
        logger.error(f"AI analysis failed for simulated vitals - patient {patient_id}: {str(e)}")
        vitals.ai_analysis = "AI analysis unavailable"
    
    vitals.save()
    
    # Create alerts if needed
    for alert_data in alerts_to_create:
        Alert.objects.create(
            patient=patient,
            type=alert_data['type'],
            message=alert_data['message'],
            severity=alert_data['severity'],
            ai_analysis=vitals.ai_analysis
        )
    
    return Response({
        'status': 'success',
        'message': 'Simulated vitals sent successfully',
        'simulated_data': simulated_data,
        'vitals': LatestVitalsSerializer(vitals).data
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description='Get current vital signs for a patient',
    manual_parameters=[
        openapi.Parameter('patient_id', openapi.IN_PATH, description="Patient ID", type=openapi.TYPE_STRING)
    ],
    responses={
        200: LatestVitalsSerializer,
        404: 'Patient or vitals not found'
    }
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])  # Allow unauthenticated access for demo and testing
def get_patient_vitals(request, patient_id):
    """Get latest vital signs for a specific patient"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    try:
        vitals = LatestVitals.objects.get(patient=patient)
        return Response(LatestVitalsSerializer(vitals).data)
    except LatestVitals.DoesNotExist:
        return Response(
            {'error': 'No vitals recorded for this patient'},
            status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='get',
    operation_description='Get all active alerts for a patient',
    manual_parameters=[
        openapi.Parameter('patient_id', openapi.IN_PATH, description="Patient ID", type=openapi.TYPE_STRING)
    ],
    responses={200: AlertSerializer(many=True)}
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])  # Allow unauthenticated access for demo and testing
def get_patient_alerts(request, patient_id):
    """Get all active alerts for a specific patient"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    alerts = Alert.objects.filter(patient=patient, is_active=True)
    
    return Response(AlertSerializer(alerts, many=True).data)


@swagger_auto_schema(
    method='patch',
    operation_description='Resolve/dismiss an alert',
    manual_parameters=[
        openapi.Parameter('alert_id', openapi.IN_PATH, description="Alert ID", type=openapi.TYPE_INTEGER)
    ],
    responses={
        200: 'Alert resolved successfully',
        404: 'Alert not found'
    }
)
@api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])  # Allow unauthenticated access for demo and testing
def resolve_alert(request, alert_id):
    """Mark an alert as resolved (inactive)"""
    alert = get_object_or_404(Alert, id=alert_id)
    alert.is_active = False
    alert.save()
    
    return Response({
        'status': 'success',
        'message': 'Alert resolved successfully',
        'alert': AlertSerializer(alert).data
    })


@swagger_auto_schema(
    method='get',
    operation_description='Get all active alerts across all patients',
    responses={200: AlertSerializer(many=True)}
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny]) #allow unauthorized access for demo and testinh
def get_all_alerts(request):
    """Get all active alerts in the system"""
    alerts = Alert.objects.filter(is_active=True).select_related('patient')
    return Response(AlertSerializer(alerts, many=True).data)


@swagger_auto_schema(
    method='get',
    operation_description='Get all devices with their current status',
    responses={200: DeviceSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_devices(request):
    """Get all devices and their status"""
    devices = Device.objects.all()
    return Response(DeviceSerializer(devices, many=True).data)


@swagger_auto_schema(
    method='post',
    operation_description='Update device status (online/offline)',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'device_id': openapi.Schema(type=openapi.TYPE_STRING),
            'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['ONLINE', 'OFFLINE']),
        },
        required=['device_id', 'status']
    ),
    responses={
        200: DeviceSerializer,
        404: 'Device not found'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def update_device_status(request):
    """Update device online/offline status"""
    device_id = request.data.get('device_id')
    new_status = request.data.get('status')
    
    if not device_id or not new_status:
        return Response(
            {'error': 'device_id and status are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_status not in ['ONLINE', 'OFFLINE']:
        return Response(
            {'error': 'status must be ONLINE or OFFLINE'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    device = get_object_or_404(Device, device_id=device_id)
    device.status = new_status
    device.save()
    
    # Create alert if device goes offline
    if new_status == 'OFFLINE':
        # Find patient associated with this bed
        try:
            patient = Patient.objects.get(bed_number=device.bed_number)
            Alert.objects.create(
                patient=patient,
                type='DEVICE_OFFLINE',
                message=f'Device {device_id} on bed {device.bed_number} is offline',
                severity='HIGH'
            )
        except Patient.DoesNotExist:
            pass  # No patient in this bed
    
    return Response(DeviceSerializer(device).data)


# Helper functions

def _assess_risk(patient, vitals):
    """
    Assess patient risk level based on vital signs.
    Returns risk_level and list of alerts to create.
    """
    alerts = []
    risk_score = 0
    
    # Check temperature
    if vitals.temperature:
        temp = float(vitals.temperature)
        if temp >= 39.0:
            risk_score += 3
            alerts.append({
                'type': 'HIGH_RISK',
                'message': f'Critical: Temperature {temp}°C - High fever detected',
                'severity': 'CRITICAL'
            })
        elif temp >= 38.5:
            risk_score += 2
            alerts.append({
                'type': 'WARNING',
                'message': f'Warning: Temperature {temp}°C - Elevated temperature',
                'severity': 'HIGH'
            })
        elif temp <= 35.0:
            risk_score += 2
            alerts.append({
                'type': 'WARNING',
                'message': f'Warning: Temperature {temp}°C - Hypothermia risk',
                'severity': 'HIGH'
            })
    
    # Check heart rate
    if vitals.heart_rate:
        hr = vitals.heart_rate
        if hr >= 120 or hr <= 50:
            risk_score += 3
            alerts.append({
                'type': 'HIGH_RISK',
                'message': f'Critical: Heart rate {hr} BPM - Abnormal heart rate',
                'severity': 'CRITICAL'
            })
        elif hr >= 100 or hr <= 60:
            risk_score += 1
            alerts.append({
                'type': 'WARNING',
                'message': f'Warning: Heart rate {hr} BPM',
                'severity': 'MEDIUM'
            })
    
    # Check SpO2
    if vitals.spo2:
        spo2 = vitals.spo2
        if spo2 < 90:
            risk_score += 4
            alerts.append({
                'type': 'HIGH_RISK',
                'message': f'Critical: SpO2 {spo2}% - Severe hypoxemia, immediate intervention required',
                'severity': 'CRITICAL'
            })
        elif spo2 < 95:
            risk_score += 2
            alerts.append({
                'type': 'WARNING',
                'message': f'Warning: SpO2 {spo2}% - Low oxygen saturation',
                'severity': 'HIGH'
            })
    
    # Determine overall risk level
    if risk_score >= 6:
        risk_level = 'CRITICAL'
    elif risk_score >= 4:
        risk_level = 'HIGH'
    elif risk_score >= 2:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return risk_level, alerts


@swagger_auto_schema(
    method='get',
    operation_description='Get dashboard summary: all patients with vitals, active alerts, and device status',
    responses={
        200: openapi.Response(
            description='Dashboard summary data',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'patients': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'alerts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'stats': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_patients': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'critical_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'high_risk_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'medium_risk_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'low_risk_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'active_alerts_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'online_devices_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_summary(request):
    """
    Get comprehensive dashboard data for frontend.
    Returns patients with vitals, active alerts, device status, and summary stats.
    """
    # Get all patients with their vitals
    patients = Patient.objects.select_related('hospital', 'latest_vitals').all()
    patients_data = PatientListSerializer(patients, many=True).data
    
    # Get active alerts
    alerts = Alert.objects.filter(is_active=True).select_related('patient').order_by('-created_at')
    alerts_data = AlertSerializer(alerts, many=True).data
    
    
    # Calculate statistics
    vitals_by_risk = LatestVitals.objects.values('risk_level').distinct()
    risk_counts = {
        'CRITICAL': LatestVitals.objects.filter(risk_level='CRITICAL').count(),
        'HIGH': LatestVitals.objects.filter(risk_level='HIGH').count(),
        'MEDIUM': LatestVitals.objects.filter(risk_level='MEDIUM').count(),
        'LOW': LatestVitals.objects.filter(risk_level='LOW').count(),
    }
    
    stats = {
        'total_patients': patients.count(),
        'critical_count': risk_counts.get('CRITICAL', 0),
        'high_risk_count': risk_counts.get('HIGH', 0),
        'medium_risk_count': risk_counts.get('MEDIUM', 0),
        'low_risk_count': risk_counts.get('LOW', 0),
        'active_alerts_count': alerts.count(),
    }
    
    return Response({
        'patients': patients_data,
        'alerts': alerts_data,
        'stats': stats
    })


@swagger_auto_schema(
    method='post',
    operation_description='Emergency alert triggered by IoT device button press',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'device_id': openapi.Schema(type=openapi.TYPE_STRING, description='Device identifier'),
            'patient_id': openapi.Schema(type=openapi.TYPE_STRING, description='Patient identifier (optional if device_id provided)'),
            'message': openapi.Schema(type=openapi.TYPE_STRING, description='Optional custom message'),
        },
        required=['device_id']
    ),
    responses={
        200: openapi.Response('Emergency alert created', AlertSerializer),
        404: 'Device or patient not found',
        400: 'Bad request'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # IoT devices don't use JWT auth
def emergency_alert(request):
    """
    Handle emergency alert from IoT device button press.
    Creates a CRITICAL alert immediately for patient assistance.
    """
    device_id = request.data.get('device_id')
    patient_id = request.data.get('patient_id')
    custom_message = request.data.get('message', '')
    
    if not device_id:
        return Response(
            {'error': 'device_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify device exists and get associated patient
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        return Response(
            {'error': f'Device {device_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get patient - either from patient_id or device's bed number
    patient = None
    if patient_id:
        patient = Patient.objects.filter(patient_id=patient_id).first()
        if not patient:
            return Response(
                {'error': f'Patient {patient_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Try to find patient by device's bed number - use first active patient in that bed
        patient = Patient.objects.filter(bed_number=device.bed_number).order_by('-id').first()
        if not patient:
            return Response(
                {'error': f'No patient found in bed {device.bed_number}'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Get current vitals for AI context (if available)
    ai_analysis = "Patient pressed emergency call button. Immediate assistance required."
    try:
        vitals = LatestVitals.objects.get(patient=patient)
        # Generate AI analysis with current vitals context
        analyzer = get_analyzer()
        ai_context = analyzer.quick_risk_assessment(vitals)
        if ai_context:
            ai_analysis = f"EMERGENCY CALL - Patient assistance requested. {ai_context}"
        else:
            ai_analysis = f"EMERGENCY CALL - Patient assistance requested. Current vitals: Temp {vitals.temperature}°C, HR {vitals.heart_rate} BPM, SpO2 {vitals.spo2}%."
    except LatestVitals.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"AI analysis failed for emergency alert: {str(e)}")
    
    # Create emergency alert
    alert_message = custom_message if custom_message else f'Emergency call button pressed - bed {device.bed_number}'
    
    alert = Alert.objects.create(
        patient=patient,
        type='HIGH_RISK',
        message=alert_message,
        severity='CRITICAL',
        ai_analysis=ai_analysis,
        is_active=True
    )
    
    logger.info(f"Emergency alert created: Patient {patient.patient_id}, Device {device_id}")
    
    return Response({
        'status': 'success',
        'message': 'Emergency alert created',
        'alert': AlertSerializer(alert).data
    }, status=status.HTTP_200_OK)


# Trend calculation commented out - requires historical vitals tracking
# def _calculate_trend(vitals):
#     """
#     Calculate vital signs trend.
#     In a real system, this would compare with historical data.
#     For now, returns a simple assessment.
#     """
#     # Simple heuristic based on current values
#     if vitals.temperature and float(vitals.temperature) > 38.0:
#         return 'RISING'
#     elif vitals.spo2 and vitals.spo2 < 93:
#         return 'FALLING'
#     else:
#         return 'STABLE'

