from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from accounts.models import UserProfile
from hospitals.models import Hospital
from patients.models import Patient
from bed_node.models import Device, LatestVitals, Alert


class BedNodeAPITests(APITestCase):
    """Test suite for bed_node API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create hospital
        self.hospital = Hospital.objects.create(name='Test Hospital')
        
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user,
            hospital=self.hospital,
            full_name='Test User'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        
        # Create test patient
        self.patient = Patient.objects.create(
            patient_id='PAT_001',
            name='John Doe',
            bed_number='101',
            ward='ICU',
            hospital=self.hospital
        )
        
        # Create test device
        self.device = Device.objects.create(
            device_id='bed_101_node',
            bed_number='101',
            status='ONLINE'
        )
    
    def test_receive_vitals(self):
        """Test receiving vitals from IoT device"""
        data = {
            'device_id': 'bed_101_node',
            'patient_id': 'PAT_001',
            'temperature': 37.5,
            'heart_rate': 75,
            'spo2': 98
        }
        
        response = self.client.post('/api/monitoring/vitals/receive/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify vitals were created
        vitals = LatestVitals.objects.get(patient=self.patient)
        self.assertEqual(float(vitals.temperature), 37.5)
        self.assertEqual(vitals.heart_rate, 75)
        self.assertEqual(vitals.spo2, 98)
    
    def test_receive_vitals_critical(self):
        """Test receiving critical vitals generates alerts"""
        data = {
            'device_id': 'bed_101_node',
            'patient_id': 'PAT_001',
            'temperature': 39.5,
            'heart_rate': 140,
            'spo2': 85
        }
        
        response = self.client.post('/api/monitoring/vitals/receive/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify alerts were created
        alerts = Alert.objects.filter(patient=self.patient, is_active=True)
        self.assertGreater(alerts.count(), 0)
        
        # Verify critical alerts exist
        critical_alerts = alerts.filter(severity='CRITICAL')
        self.assertGreater(critical_alerts.count(), 0)
    
    def test_simulate_vitals(self):
        """Test simulating vitals data"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        data = {
            'device_id': 'bed_101_node',
            'patient_id': 'PAT_001'
        }
        
        response = self.client.post('/api/monitoring/vitals/simulate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify vitals were created with simulated data
        vitals = LatestVitals.objects.get(patient=self.patient)
        self.assertIsNotNone(vitals.temperature)
        self.assertIsNotNone(vitals.heart_rate)
        self.assertIsNotNone(vitals.spo2)
    
    def test_get_patient_vitals(self):
        """Test getting patient vitals"""
        # Create vitals first
        LatestVitals.objects.create(
            patient=self.patient,
            temperature=Decimal('37.0'),
            heart_rate=70,
            spo2=98
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/monitoring/patients/PAT_001/vitals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['patient_id'], 'PAT_001')
        self.assertEqual(float(response.data['temperature']), 37.0)
    
    def test_get_patient_alerts(self):
        """Test getting patient alerts"""
        # Create alerts
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Test alert',
            severity='MEDIUM',
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/monitoring/patients/PAT_001/alerts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'WARNING')
    
    def test_resolve_alert(self):
        """Test resolving an alert"""
        alert = Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Test alert',
            severity='MEDIUM',
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.patch(f'/api/monitoring/alerts/{alert.id}/resolve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify alert is resolved
        alert.refresh_from_db()
        self.assertFalse(alert.is_active)
    
    def test_get_all_alerts(self):
        """Test getting all active alerts"""
        Alert.objects.create(
            patient=self.patient,
            type='HIGH_RISK',
            message='Critical alert',
            severity='CRITICAL',
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/monitoring/alerts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_get_devices(self):
        """Test getting all devices"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/monitoring/devices/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['device_id'], 'bed_101_node')
    
    def test_update_device_status(self):
        """Test updating device status"""
        data = {
            'device_id': 'bed_101_node',
            'status': 'OFFLINE'
        }
        
        response = self.client.post('/api/monitoring/device/status/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify device status updated
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, 'OFFLINE')
        
        # Verify offline alert was created
        offline_alerts = Alert.objects.filter(
            patient=self.patient,
            type='DEVICE_OFFLINE'
        )
        self.assertEqual(offline_alerts.count(), 1)
    
    def test_authentication_required(self):
        """Test endpoints require authentication"""
        # Try without authentication
        response = self.client.get('/api/monitoring/devices/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/monitoring/alerts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_device_id(self):
        """Test receiving vitals with invalid device"""
        data = {
            'device_id': 'invalid_device',
            'patient_id': 'PAT_001',
            'temperature': 37.0,
            'heart_rate': 70,
            'spo2': 98
        }
        
        response = self.client.post('/api/monitoring/vitals/receive/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_patient_id(self):
        """Test receiving vitals with invalid patient"""
        data = {
            'device_id': 'bed_101_node',
            'patient_id': 'INVALID_PAT',
            'temperature': 37.0,
            'heart_rate': 70,
            'spo2': 98
        }
        
        response = self.client.post('/api/monitoring/vitals/receive/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
