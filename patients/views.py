from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Prefetch

from .models import Patient
from .serializers import PatientListSerializer, PatientDetailSerializer
from bed_node.models import LatestVitals


@swagger_auto_schema(
    method='get',
    operation_description='Get list of all patients with optional risk level filtering',
    manual_parameters=[
        openapi.Parameter(
            'risk_level',
            openapi.IN_QUERY,
            description="Filter by risk level: LOW, MEDIUM, HIGH, CRITICAL",
            type=openapi.TYPE_STRING,
            enum=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        ),
        openapi.Parameter(
            'ward',
            openapi.IN_QUERY,
            description="Filter by ward",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'bed_number',
            openapi.IN_QUERY,
            description="Filter by bed number",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={200: PatientListSerializer(many=True)}
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def patient_list(request):
    """
    Get list of all patients with their current vitals and risk levels.
    Supports filtering by risk_level, ward, and bed_number.
    """
    # Get all patients with prefetched vitals for efficiency
    patients = Patient.objects.select_related('hospital').prefetch_related(
        Prefetch('latest_vitals', queryset=LatestVitals.objects.all())
    ).all()
    
    # Apply filters
    risk_level = request.query_params.get('risk_level')
    ward = request.query_params.get('ward')
    bed_number = request.query_params.get('bed_number')
    
    if ward:
        patients = patients.filter(ward__icontains=ward)
    
    if bed_number:
        patients = patients.filter(bed_number=bed_number)
    
    # Serialize patients
    serializer = PatientListSerializer(patients, many=True)
    patient_data = serializer.data
    
    # Filter by risk level (after serialization since risk_level is in LatestVitals)
    if risk_level:
        risk_level_upper = risk_level.upper()
        patient_data = [
            p for p in patient_data
            if p.get('risk_level', '').upper() == risk_level_upper
        ]
    
    return Response({
        'count': len(patient_data),
        'patients': patient_data
    })


@swagger_auto_schema(
    method='get',
    operation_description='Get detailed information for a specific patient',
    manual_parameters=[
        openapi.Parameter(
            'patient_id',
            openapi.IN_PATH,
            description="Patient ID",
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        200: PatientDetailSerializer,
        404: 'Patient not found'
    }
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def patient_detail(request, patient_id):
    """Get detailed information for a specific patient"""
    patient = get_object_or_404(
        Patient.objects.select_related('hospital'),
        patient_id=patient_id
    )
    
    serializer = PatientDetailSerializer(patient)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description='Get patients grouped by risk level',
    responses={
        200: openapi.Response(
            description='Patients grouped by risk level',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'critical': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                    'high': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                    'medium': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                    'low': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                }
            )
        )
    }
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def patients_by_risk(request):
    """
    Get patients grouped by their risk levels.
    Useful for dashboard overview.
    """
    # Get all patients with vitals
    patients = Patient.objects.select_related('hospital').prefetch_related(
        Prefetch('latest_vitals', queryset=LatestVitals.objects.all())
    ).all()
    
    serializer = PatientListSerializer(patients, many=True)
    all_patients = serializer.data
    
    # Group by risk level
    grouped = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': [],
        'unknown': []  # Patients without vitals
    }
    
    for patient in all_patients:
        risk = patient.get('risk_level', '').upper()
        if risk == 'CRITICAL':
            grouped['critical'].append(patient)
        elif risk == 'HIGH':
            grouped['high'].append(patient)
        elif risk == 'MEDIUM':
            grouped['medium'].append(patient)
        elif risk == 'LOW':
            grouped['low'].append(patient)
        else:
            grouped['unknown'].append(patient)
    
    return Response({
        'summary': {
            'critical_count': len(grouped['critical']),
            'high_count': len(grouped['high']),
            'medium_count': len(grouped['medium']),
            'low_count': len(grouped['low']),
            'unknown_count': len(grouped['unknown']),
            'total_count': len(all_patients)
        },
        'patients': grouped
    })

