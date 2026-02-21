from django.test import TestCase
from django.db import IntegrityError
from .models import Patient
from hospitals.models import Hospital


class PatientModelTest(TestCase):
    """Test cases for Patient model"""
    
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Test Hospital")
        self.hospital2 = Hospital.objects.create(name="Another Hospital")
    
    def test_create_patient_with_all_fields(self):
        """Test creating a patient with all fields"""
        patient = Patient.objects.create(
            patient_id='PAT_0001',
            name='John Doe',
            bed_number='101',
            ward='ICU',
            hospital=self.hospital
        )
        
        self.assertEqual(patient.patient_id, 'PAT_0001')
        self.assertEqual(patient.name, 'John Doe')
        self.assertEqual(patient.bed_number, '101')
        self.assertEqual(patient.ward, 'ICU')
        self.assertEqual(patient.hospital, self.hospital)
        self.assertIsNotNone(patient.created_at)
    
    def test_create_patient_without_name(self):
        """Test creating a patient without name (optional field)"""
        patient = Patient.objects.create(
            patient_id='PAT_0002',
            bed_number='102',
            ward='Emergency',
            hospital=self.hospital
        )
        
        self.assertEqual(patient.patient_id, 'PAT_0002')
        self.assertIsNone(patient.name)
        self.assertEqual(patient.bed_number, '102')
        self.assertEqual(patient.ward, 'Emergency')
    
    def test_patient_string_representation_with_name(self):
        """Test string representation of patient with name"""
        patient = Patient.objects.create(
            patient_id='PAT_0003',
            name='Jane Smith',
            bed_number='103',
            ward='General',
            hospital=self.hospital
        )
        
        expected = "PAT_0003 - Jane Smith (Bed 103)"
        self.assertEqual(str(patient), expected)
    
    def test_patient_string_representation_without_name(self):
        """Test string representation of patient without name"""
        patient = Patient.objects.create(
            patient_id='PAT_0004',
            bed_number='104',
            ward='Pediatrics',
            hospital=self.hospital
        )
        
        expected = "PAT_0004 - Demo Patient (Bed 104)"
        self.assertEqual(str(patient), expected)
    
    def test_patient_id_must_be_unique(self):
        """Test that patient_id must be unique across all hospitals"""
        Patient.objects.create(
            patient_id='PAT_0005',
            bed_number='105',
            ward='ICU',
            hospital=self.hospital
        )
        
        # Try to create another patient with same patient_id
        with self.assertRaises(IntegrityError):
            Patient.objects.create(
                patient_id='PAT_0005',
                bed_number='106',
                ward='Emergency',
                hospital=self.hospital2
            )
    
    def test_bed_number_unique_per_hospital(self):
        """Test that bed numbers are unique within a hospital"""
        Patient.objects.create(
            patient_id='PAT_0006',
            bed_number='107',
            ward='ICU',
            hospital=self.hospital
        )
        
        # Try to create another patient with same bed in same hospital
        with self.assertRaises(IntegrityError):
            Patient.objects.create(
                patient_id='PAT_0007',
                bed_number='107',
                ward='ICU',
                hospital=self.hospital
            )
    
    def test_same_bed_number_different_hospitals(self):
        """Test that same bed number can exist in different hospitals"""
        patient1 = Patient.objects.create(
            patient_id='PAT_0008',
            bed_number='108',
            ward='ICU',
            hospital=self.hospital
        )
        
        patient2 = Patient.objects.create(
            patient_id='PAT_0009',
            bed_number='108',
            ward='Emergency',
            hospital=self.hospital2
        )
        
        self.assertEqual(patient1.bed_number, patient2.bed_number)
        self.assertNotEqual(patient1.hospital, patient2.hospital)
    
    def test_patient_hospital_relationship(self):
        """Test relationship between patient and hospital"""
        patient = Patient.objects.create(
            patient_id='PAT_0010',
            bed_number='109',
            ward='General',
            hospital=self.hospital
        )
        
        # Test reverse relationship
        self.assertIn(patient, self.hospital.patients.all())
        self.assertEqual(self.hospital.patients.count(), 1)
    
    def test_multiple_patients_in_same_ward(self):
        """Test multiple patients can be in the same ward"""
        patient1 = Patient.objects.create(
            patient_id='PAT_0011',
            bed_number='110',
            ward='ICU',
            hospital=self.hospital
        )
        
        patient2 = Patient.objects.create(
            patient_id='PAT_0012',
            bed_number='111',
            ward='ICU',
            hospital=self.hospital
        )
        
        icu_patients = Patient.objects.filter(ward='ICU', hospital=self.hospital)
        self.assertEqual(icu_patients.count(), 2)
        self.assertIn(patient1, icu_patients)
        self.assertIn(patient2, icu_patients)
    
    def test_patient_ordering(self):
        """Test patients are ordered by created_at descending"""
        from time import sleep
        
        patient1 = Patient.objects.create(
            patient_id='PAT_0013',
            bed_number='112',
            ward='ICU',
            hospital=self.hospital
        )
        
        sleep(0.01)  # Small delay to ensure different timestamps
        
        patient2 = Patient.objects.create(
            patient_id='PAT_0014',
            bed_number='113',
            ward='ICU',
            hospital=self.hospital
        )
        
        patients = Patient.objects.filter(
            patient_id__in=['PAT_0013', 'PAT_0014']
        )
        self.assertEqual(patients[0], patient2)  # Most recent first
        self.assertEqual(patients[1], patient1)
    
    def test_delete_hospital_cascades_to_patients(self):
        """Test that deleting a hospital deletes its patients"""
        patient = Patient.objects.create(
            patient_id='PAT_0015',
            bed_number='114',
            ward='ICU',
            hospital=self.hospital
        )
        
        hospital_id = self.hospital.id
        self.hospital.delete()
        
        # Patient should be deleted
        self.assertFalse(Patient.objects.filter(patient_id='PAT_0015').exists())
    
    def test_create_patient_with_medical_records(self):
        """Test creating a patient with past medical records"""
        medical_history = "Diabetes, Hypertension, Previous heart surgery in 2023"
        patient = Patient.objects.create(
            patient_id='PAT_0016',
            name='Medical Patient',
            bed_number='115',
            ward='Cardiology',
            hospital=self.hospital,
            past_medical_records=medical_history
        )
        
        self.assertEqual(patient.past_medical_records, medical_history)
    
    def test_patient_without_medical_records(self):
        """Test that past_medical_records is optional"""
        patient = Patient.objects.create(
            patient_id='PAT_0017',
            bed_number='116',
            ward='Emergency',
            hospital=self.hospital
        )
        
        self.assertIsNone(patient.past_medical_records)
