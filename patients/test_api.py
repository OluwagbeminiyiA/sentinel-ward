from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from accounts.models import UserProfile
from hospitals.models import Hospital
from patients.models import Patient
from bed_node.models import LatestVitals


class PatientAPITests(APITestCase):
    """Test suite for patient API endpoints"""
    
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
        
        # Create test patients
        self.patient1 = Patient.objects.create(
            patient_id='PAT_001',
            name='John Doe',
            bed_number='101',
            ward='ICU',
            hospital=self.hospital
        )
        
        self.patient2 = Patient.objects.create(
            patient_id='PAT_002',
            name='Jane Smith',
            bed_number='102',
            ward='ICU',
            hospital=self.hospital
        )
        
        self.patient3 = Patient.objects.create(
            patient_id='PAT_003',
            name='Bob Wilson',
            bed_number='201',
            ward='General',
            hospital=self.hospital
        )
        
        # Create vitals with different risk levels
        LatestVitals.objects.create(
            patient=self.patient1,
            temperature=Decimal('39.5'),
            heart_rate=130,
            spo2=88,
            risk_level='CRITICAL',
            trend='FALLING'
        )
        
        LatestVitals.objects.create(
            patient=self.patient2,
            temperature=Decimal('38.8'),
            heart_rate=95,
            spo2=93,
            risk_level='HIGH',
            trend='RISING'
        )
        
        LatestVitals.objects.create(
            patient=self.patient3,
            temperature=Decimal('37.2'),
            heart_rate=72,
            spo2=98,
            risk_level='LOW',
            trend='STABLE'
        )
    
    def test_patient_list(self):
        """Test getting list of all patients"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['patients']), 3)
    
    def test_patient_list_filter_by_risk_critical(self):
        """Test filtering patients by CRITICAL risk level"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?risk_level=CRITICAL')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['patients'][0]['patient_id'], 'PAT_001')
        self.assertEqual(response.data['patients'][0]['risk_level'], 'CRITICAL')
    
    def test_patient_list_filter_by_risk_high(self):
        """Test filtering patients by HIGH risk level"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?risk_level=HIGH')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['patients'][0]['patient_id'], 'PAT_002')
    
    def test_patient_list_filter_by_risk_low(self):
        """Test filtering patients by LOW risk level"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?risk_level=LOW')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['patients'][0]['patient_id'], 'PAT_003')
    
    def test_patient_list_filter_by_ward(self):
        """Test filtering patients by ward"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?ward=ICU')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_patient_list_filter_by_bed_number(self):
        """Test filtering patients by bed number"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?bed_number=101')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['patients'][0]['bed_number'], '101')
    
    def test_patient_list_includes_vitals(self):
        """Test patient list includes vital signs data"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        patient = response.data['patients'][0]
        
        # Check vitals fields are present
        self.assertIn('temperature', patient)
        self.assertIn('heart_rate', patient)
        self.assertIn('spo2', patient)
        self.assertIn('risk_level', patient)
        self.assertIn('trend', patient)
    
    def test_patient_detail(self):
        """Test getting detailed patient information"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/PAT_001/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['patient_id'], 'PAT_001')
        self.assertEqual(response.data['name'], 'John Doe')
        self.assertEqual(response.data['bed_number'], '101')
        self.assertEqual(response.data['ward'], 'ICU')
    
    def test_patient_detail_not_found(self):
        """Test getting non-existent patient"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/PAT_999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_patients_by_risk_grouped(self):
        """Test getting patients grouped by risk level"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/risk/grouped/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check summary counts
        summary = response.data['summary']
        self.assertEqual(summary['critical_count'], 1)
        self.assertEqual(summary['high_count'], 1)
        self.assertEqual(summary['low_count'], 1)
        self.assertEqual(summary['total_count'], 3)
        
        # Check grouped patients
        patients = response.data['patients']
        self.assertEqual(len(patients['critical']), 1)
        self.assertEqual(len(patients['high']), 1)
        self.assertEqual(len(patients['low']), 1)
        
        # Verify correct patients in groups
        self.assertEqual(patients['critical'][0]['patient_id'], 'PAT_001')
        self.assertEqual(patients['high'][0]['patient_id'], 'PAT_002')
        self.assertEqual(patients['low'][0]['patient_id'], 'PAT_003')
    
    def test_patients_without_vitals(self):
        """Test patient list handles patients without vitals"""
        # Create patient without vitals
        patient_no_vitals = Patient.objects.create(
            patient_id='PAT_004',
            name='No Vitals Patient',
            bed_number='301',
            ward='General',
            hospital=self.hospital
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        
        # Find the patient without vitals
        no_vitals = [p for p in response.data['patients'] if p['patient_id'] == 'PAT_004'][0]
        self.assertIsNone(no_vitals['temperature'])
        self.assertIsNone(no_vitals['heart_rate'])
        self.assertIsNone(no_vitals['spo2'])
        self.assertEqual(no_vitals['risk_level'], '')
    
    def test_patients_by_risk_with_unknown(self):
        """Test grouped patients includes unknown risk category"""
        # Create patient without vitals
        Patient.objects.create(
            patient_id='PAT_005',
            bed_number='302',
            ward='General',
            hospital=self.hospital
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/risk/grouped/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['unknown_count'], 1)
        self.assertEqual(len(response.data['patients']['unknown']), 1)
    
    def test_authentication_required(self):
        """Test endpoints require authentication"""
        # Try without authentication
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/patients/PAT_001/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/patients/risk/grouped/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_combined_filters(self):
        """Test combining multiple filters"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?ward=ICU&risk_level=CRITICAL')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['patients'][0]['patient_id'], 'PAT_001')
        self.assertEqual(response.data['patients'][0]['ward'], 'ICU')
    
    def test_patient_list_includes_hospital_name(self):
        """Test patient list includes hospital name"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        patient = response.data['patients'][0]
        self.assertEqual(patient['hospital_name'], 'Test Hospital')
    
    def test_case_insensitive_ward_filter(self):
        """Test ward filter is case insensitive"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?ward=icu')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_patient_vitals_trend_displayed(self):
        """Test patient list shows vitals trend"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/patients/?patient_id=PAT_001')
        
        # Get patient 1 from results
        patients = response.data['patients']
        patient1 = [p for p in patients if p['patient_id'] == 'PAT_001'][0]
        
        self.assertEqual(patient1['trend'], 'FALLING')
