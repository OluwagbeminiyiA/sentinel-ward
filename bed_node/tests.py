from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
import json
from .models import Device, LatestVitals, Prediction, Alert
from patients.models import Patient
from hospitals.models import Hospital


class DeviceModelTests(TestCase):
    """Test suite for Device model"""
    
    def setUp(self):
        """Set up test data"""
        self.device = Device.objects.create(
            device_id='bed_12_node',
            bed_number='12',
            status='ONLINE'
        )
    
    def test_device_creation(self):
        """Test basic device creation"""
        self.assertEqual(self.device.device_id, 'bed_12_node')
        self.assertEqual(self.device.bed_number, '12')
        self.assertEqual(self.device.status, 'ONLINE')
        self.assertIsNotNone(self.device.last_seen)
    
    def test_device_id_unique(self):
        """Test device_id uniqueness constraint"""
        with self.assertRaises(Exception):
            Device.objects.create(
                device_id='bed_12_node',
                bed_number='13',
                status='ONLINE'
            )
    
    def test_default_status_offline(self):
        """Test default status is OFFLINE"""
        device = Device.objects.create(
            device_id='bed_15_node',
            bed_number='15'
        )
        self.assertEqual(device.status, 'OFFLINE')
    
    def test_status_choices(self):
        """Test valid status values"""
        self.device.status = 'ONLINE'
        self.device.save()
        self.assertEqual(self.device.status, 'ONLINE')
        
        self.device.status = 'OFFLINE'
        self.device.save()
        self.assertEqual(self.device.status, 'OFFLINE')
    
    def test_last_seen_auto_update(self):
        """Test last_seen updates automatically"""
        old_time = self.device.last_seen
        self.device.bed_number = '13'
        self.device.save()
        self.assertGreaterEqual(self.device.last_seen, old_time)
    
    def test_string_representation(self):
        """Test __str__ method"""
        expected = "bed_12_node (Bed 12) - ONLINE"
        self.assertEqual(str(self.device), expected)
    
    def test_device_with_different_bed_numbers(self):
        """Test multiple devices with different bed numbers"""
        device2 = Device.objects.create(
            device_id='bed_20_node',
            bed_number='20',
            status='OFFLINE'
        )
        self.assertEqual(Device.objects.count(), 2)
        self.assertNotEqual(self.device.bed_number, device2.bed_number)
    
    def test_device_ordering(self):
        """Test devices are ordered by bed_number and device_id"""
        Device.objects.create(
            device_id='bed_01_node',
            bed_number='01',
            status='ONLINE'
        )
        Device.objects.create(
            device_id='bed_05_node',
            bed_number='05',
            status='OFFLINE'
        )
        
        devices = Device.objects.all()
        self.assertEqual(devices[0].bed_number, '01')
        self.assertEqual(devices[1].bed_number, '05')
        self.assertEqual(devices[2].bed_number, '12')
    
    def test_last_seen_timezone_aware(self):
        """Test last_seen is timezone aware"""
        self.assertIsNotNone(self.device.last_seen.tzinfo)
    
    def test_device_id_max_length(self):
        """Test device_id respects max_length"""
        long_id = 'a' * 100
        device = Device.objects.create(
            device_id=long_id,
            bed_number='99'
        )
        self.assertEqual(len(device.device_id), 100)
    
    def test_bed_number_field(self):
        """Test bed_number field accepts various formats"""
        test_cases = ['A1', '101', 'ICU-5', '3B']
        for i, bed in enumerate(test_cases):
            device = Device.objects.create(
                device_id=f'test_node_{i}',
                bed_number=bed
            )
            self.assertEqual(device.bed_number, bed)
    
    def test_multiple_devices_per_bed(self):
        """Test multiple devices can be associated with same bed"""
        device2 = Device.objects.create(
            device_id='bed_12_sensor',
            bed_number='12',
            status='ONLINE'
        )
        devices_on_bed_12 = Device.objects.filter(bed_number='12')
        self.assertEqual(devices_on_bed_12.count(), 2)


class LatestVitalsModelTests(TestCase):
    """Test suite for LatestVitals model"""
    
    def setUp(self):
        """Set up test data"""
        self.hospital = Hospital.objects.create(name='Test Hospital')
        self.patient = Patient.objects.create(
            patient_id='PAT_001',
            name='John Doe',
            bed_number='101',
            ward='ICU',
            hospital=self.hospital
        )
        self.vitals = LatestVitals.objects.create(
            patient=self.patient,
            temperature=Decimal('37.5'),
            heart_rate=75,
            spo2=98,
            risk_level='LOW',
            trend='STABLE'
        )
    
    def test_vitals_creation(self):
        """Test basic vitals creation"""
        self.assertEqual(self.vitals.patient, self.patient)
        self.assertEqual(self.vitals.temperature, Decimal('37.5'))
        self.assertEqual(self.vitals.heart_rate, 75)
        self.assertEqual(self.vitals.spo2, 98)
        self.assertEqual(self.vitals.risk_level, 'LOW')
        self.assertEqual(self.vitals.trend, 'STABLE')
        self.assertIsNotNone(self.vitals.updated_at)
    
    def test_one_to_one_relationship(self):
        """Test one patient can only have one latest vitals record"""
        with self.assertRaises(Exception):
            LatestVitals.objects.create(
                patient=self.patient,
                temperature=Decimal('38.0'),
                heart_rate=80
            )
    
    def test_vitals_optional_fields(self):
        """Test vitals can be created with minimal data"""
        patient2 = Patient.objects.create(
            patient_id='PAT_002',
            bed_number='102',
            ward='General',
            hospital=self.hospital
        )
        vitals = LatestVitals.objects.create(patient=patient2)
        self.assertIsNone(vitals.temperature)
        self.assertIsNone(vitals.heart_rate)
        self.assertIsNone(vitals.spo2)
        self.assertEqual(vitals.risk_level, '')
        self.assertEqual(vitals.trend, 'STABLE')
    
    def test_default_trend_stable(self):
        """Test default trend is STABLE"""
        patient2 = Patient.objects.create(
            patient_id='PAT_003',
            bed_number='103',
            ward='ICU',
            hospital=self.hospital
        )
        vitals = LatestVitals.objects.create(patient=patient2)
        self.assertEqual(vitals.trend, 'STABLE')
    
    def test_trend_choices(self):
        """Test valid trend values"""
        self.vitals.trend = 'RISING'
        self.vitals.save()
        self.assertEqual(self.vitals.trend, 'RISING')
        
        self.vitals.trend = 'FALLING'
        self.vitals.save()
        self.assertEqual(self.vitals.trend, 'FALLING')
        
        self.vitals.trend = 'STABLE'
        self.vitals.save()
        self.assertEqual(self.vitals.trend, 'STABLE')
    
    def test_updated_at_auto_update(self):
        """Test updated_at updates automatically"""
        old_time = self.vitals.updated_at
        self.vitals.heart_rate = 80
        self.vitals.save()
        self.assertGreaterEqual(self.vitals.updated_at, old_time)
    
    def test_string_representation_with_name(self):
        """Test __str__ method with patient name"""
        result = str(self.vitals)
        self.assertIn('John Doe', result)
        self.assertIn('STABLE', result)
    
    def test_string_representation_without_name(self):
        """Test __str__ method without patient name"""
        patient2 = Patient.objects.create(
            patient_id='PAT_004',
            bed_number='104',
            ward='General',
            hospital=self.hospital
        )
        vitals = LatestVitals.objects.create(patient=patient2)
        result = str(vitals)
        self.assertIn('PAT_004', result)
    
    def test_cascade_delete(self):
        """Test vitals are deleted when patient is deleted"""
        patient_id = self.patient.id
        self.patient.delete()
        self.assertFalse(LatestVitals.objects.filter(patient_id=patient_id).exists())
    
    def test_related_name_access(self):
        """Test accessing vitals from patient using related_name"""
        self.assertEqual(self.patient.latest_vitals, self.vitals)
    
    def test_temperature_decimal_precision(self):
        """Test temperature stores correct decimal precision"""
        self.vitals.temperature = Decimal('38.75')
        self.vitals.save()
        self.vitals.refresh_from_db()
        self.assertEqual(self.vitals.temperature, Decimal('38.8'))  # One decimal place
    
    def test_heart_rate_range(self):
        """Test heart rate accepts valid ranges"""
        test_values = [40, 60, 80, 100, 150, 200]
        for hr in test_values:
            self.vitals.heart_rate = hr
            self.vitals.save()
            self.vitals.refresh_from_db()
            self.assertEqual(self.vitals.heart_rate, hr)
    
    def test_spo2_percentage(self):
        """Test SpO2 accepts percentage values"""
        test_values = [85, 90, 95, 98, 100]
        for spo2 in test_values:
            self.vitals.spo2 = spo2
            self.vitals.save()
            self.vitals.refresh_from_db()
            self.assertEqual(self.vitals.spo2, spo2)
    
    def test_risk_level_values(self):
        """Test various risk level values"""
        risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', '']
        for level in risk_levels:
            self.vitals.risk_level = level
            self.vitals.save()
            self.vitals.refresh_from_db()
            self.assertEqual(self.vitals.risk_level, level)
    
    def test_vitals_ordering(self):
        """Test vitals are ordered by updated_at descending"""
        patient2 = Patient.objects.create(
            patient_id='PAT_005',
            bed_number='105',
            ward='ICU',
            hospital=self.hospital
        )
        vitals2 = LatestVitals.objects.create(
            patient=patient2,
            heart_rate=85
        )
        
        # Verify both vitals exist
        all_vitals = list(LatestVitals.objects.all())
        self.assertEqual(len(all_vitals), 2)
        # Most recent should be first (ordering by -updated_at)
        self.assertIn(vitals2, all_vitals)
        self.assertIn(self.vitals, all_vitals)
    
    def test_update_existing_vitals(self):
        """Test updating existing vitals record"""
        self.vitals.temperature = Decimal('39.0')
        self.vitals.heart_rate = 95
        self.vitals.spo2 = 94
        self.vitals.risk_level = 'HIGH'
        self.vitals.trend = 'RISING'
        self.vitals.save()
        
        self.vitals.refresh_from_db()
        self.assertEqual(self.vitals.temperature, Decimal('39.0'))
        self.assertEqual(self.vitals.heart_rate, 95)
        self.assertEqual(self.vitals.spo2, 94)
        self.assertEqual(self.vitals.risk_level, 'HIGH')
        self.assertEqual(self.vitals.trend, 'RISING')


class PredictionModelTests(TestCase):
    """Test suite for Prediction model"""
    
    def setUp(self):
        """Set up test data"""
        self.hospital = Hospital.objects.create(name='Test Hospital')
        self.patient = Patient.objects.create(
            patient_id='PAT_001',
            name='Jane Smith',
            bed_number='201',
            ward='ICU',
            hospital=self.hospital
        )
        self.prediction = Prediction.objects.create(
            patient=self.patient,
            risk_level='HIGH',
            confidence=Decimal('87.50'),
            drivers='{"temperature": "elevated", "heart_rate": "abnormal"}'
        )
    
    def test_prediction_creation(self):
        """Test basic prediction creation"""
        self.assertEqual(self.prediction.patient, self.patient)
        self.assertEqual(self.prediction.risk_level, 'HIGH')
        self.assertEqual(self.prediction.confidence, Decimal('87.50'))
        self.assertIn('temperature', self.prediction.drivers)
        self.assertIsNotNone(self.prediction.created_at)
    
    def test_multiple_predictions_per_patient(self):
        """Test patient can have multiple predictions"""
        prediction2 = Prediction.objects.create(
            patient=self.patient,
            risk_level='MEDIUM',
            confidence=Decimal('75.00')
        )
        predictions = Prediction.objects.filter(patient=self.patient)
        self.assertEqual(predictions.count(), 2)
    
    def test_cascade_delete(self):
        """Test predictions are deleted when patient is deleted"""
        patient_id = self.patient.id
        self.patient.delete()
        self.assertFalse(Prediction.objects.filter(patient_id=patient_id).exists())
    
    def test_related_name_access(self):
        """Test accessing predictions from patient"""
        predictions = self.patient.predictions.all()
        self.assertIn(self.prediction, predictions)
    
    def test_confidence_precision(self):
        """Test confidence stores correct decimal precision"""
        self.prediction.confidence = Decimal('99.99')
        self.prediction.save()
        self.prediction.refresh_from_db()
        self.assertEqual(self.prediction.confidence, Decimal('99.99'))
    
    def test_confidence_range(self):
        """Test confidence accepts valid percentage ranges"""
        test_values = [Decimal('0.00'), Decimal('50.00'), Decimal('99.99'), Decimal('100.00')]
        for conf in test_values:
            self.prediction.confidence = conf
            self.prediction.save()
            self.prediction.refresh_from_db()
            self.assertEqual(self.prediction.confidence, conf)
    
    def test_risk_level_values(self):
        """Test various risk level values"""
        risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        for level in risk_levels:
            self.prediction.risk_level = level
            self.prediction.save()
            self.prediction.refresh_from_db()
            self.assertEqual(self.prediction.risk_level, level)
    
    def test_drivers_json_storage(self):
        """Test drivers can store JSON data"""
        drivers_data = {
            'vital_signs': ['temperature', 'heart_rate'],
            'severity': 'high',
            'factors': ['age', 'pre-existing conditions']
        }
        self.prediction.drivers = json.dumps(drivers_data)
        self.prediction.save()
        self.prediction.refresh_from_db()
        
        loaded_data = json.loads(self.prediction.drivers)
        self.assertEqual(loaded_data['severity'], 'high')
        self.assertIn('temperature', loaded_data['vital_signs'])
    
    def test_drivers_text_storage(self):
        """Test drivers can store plain text"""
        text_drivers = "Patient shows elevated temperature and irregular heart rate"
        self.prediction.drivers = text_drivers
        self.prediction.save()
        self.prediction.refresh_from_db()
        self.assertEqual(self.prediction.drivers, text_drivers)
    
    def test_empty_drivers(self):
        """Test prediction can have empty drivers"""
        prediction = Prediction.objects.create(
            patient=self.patient,
            risk_level='LOW',
            confidence=Decimal('95.00')
        )
        self.assertEqual(prediction.drivers, '')
    
    def test_string_representation_with_name(self):
        """Test __str__ method with patient name"""
        result = str(self.prediction)
        self.assertIn('Jane Smith', result)
        self.assertIn('HIGH', result)
        self.assertIn('87.5', result)
    
    def test_string_representation_without_name(self):
        """Test __str__ method without patient name"""
        patient2 = Patient.objects.create(
            patient_id='PAT_999',
            bed_number='999',
            ward='General',
            hospital=self.hospital
        )
        prediction = Prediction.objects.create(
            patient=patient2,
            risk_level='LOW',
            confidence=Decimal('92.00')
        )
        result = str(prediction)
        self.assertIn('PAT_999', result)
    
    def test_prediction_ordering(self):
        """Test predictions are ordered by created_at descending"""
        prediction2 = Prediction.objects.create(
            patient=self.patient,
            risk_level='MEDIUM',
            confidence=Decimal('80.00')
        )
        
        all_predictions = list(Prediction.objects.filter(patient=self.patient))
        # Most recent should appear first
        self.assertEqual(len(all_predictions), 2)
        self.assertIn(prediction2, all_predictions)
        self.assertIn(self.prediction, all_predictions)
    
    def test_created_at_auto_now_add(self):
        """Test created_at is set automatically and doesn't change"""
        original_time = self.prediction.created_at
        self.prediction.risk_level = 'MEDIUM'
        self.prediction.save()
        self.prediction.refresh_from_db()
        self.assertEqual(self.prediction.created_at, original_time)
    
    def test_created_at_timezone_aware(self):
        """Test created_at is timezone aware"""
        self.assertIsNotNone(self.prediction.created_at.tzinfo)
    
    def test_multiple_patients_predictions(self):
        """Test predictions for different patients"""
        patient2 = Patient.objects.create(
            patient_id='PAT_002',
            bed_number='202',
            ward='General',
            hospital=self.hospital
        )
        prediction2 = Prediction.objects.create(
            patient=patient2,
            risk_level='LOW',
            confidence=Decimal('92.00')
        )
        
        patient1_predictions = Prediction.objects.filter(patient=self.patient)
        patient2_predictions = Prediction.objects.filter(patient=patient2)
        
        self.assertEqual(patient1_predictions.count(), 1)
        self.assertEqual(patient2_predictions.count(), 1)
        self.assertNotEqual(patient1_predictions[0].patient, patient2_predictions[0].patient)
    
    def test_high_confidence_prediction(self):
        """Test prediction with very high confidence"""
        prediction = Prediction.objects.create(
            patient=self.patient,
            risk_level='CRITICAL',
            confidence=Decimal('99.99'),
            drivers='{"all_vitals": "critical", "immediate_action_required": true}'
        )
        self.assertEqual(prediction.confidence, Decimal('99.99'))
        self.assertEqual(prediction.risk_level, 'CRITICAL')
    
    def test_low_confidence_prediction(self):
        """Test prediction with low confidence"""
        prediction = Prediction.objects.create(
            patient=self.patient,
            risk_level='MEDIUM',
            confidence=Decimal('15.50'),
            drivers='{"insufficient_data": true}'
        )
        self.assertEqual(prediction.confidence, Decimal('15.50'))
    
    def test_prediction_history(self):
        """Test tracking prediction history for a patient"""
        # Create multiple predictions over time
        Prediction.objects.create(
            patient=self.patient,
            risk_level='LOW',
            confidence=Decimal('90.00')
        )
        Prediction.objects.create(
            patient=self.patient,
            risk_level='MEDIUM',
            confidence=Decimal('85.00')
        )
        Prediction.objects.create(
            patient=self.patient,
            risk_level='HIGH',
            confidence=Decimal('95.00')
        )
        
        history = self.patient.predictions.all()
        self.assertEqual(history.count(), 4)  # Including the one from setUp
        
        # Verify ordering (most recent first)
        risk_levels = [p.risk_level for p in history]
        self.assertEqual(len(risk_levels), 4)


class AlertModelTests(TestCase):
    """Test suite for Alert model"""
    
    def setUp(self):
        """Set up test data"""
        self.hospital = Hospital.objects.create(name='Test Hospital')
        self.patient = Patient.objects.create(
            patient_id='PAT_001',
            name='John Doe',
            bed_number='101',
            ward='ICU',
            hospital=self.hospital
        )
        self.alert = Alert.objects.create(
            patient=self.patient,
            type='HIGH_RISK',
            message='Patient vital signs showing critical deterioration',
            severity='CRITICAL',
            is_active=True
        )
    
    def test_alert_creation(self):
        """Test basic alert creation"""
        self.assertEqual(self.alert.patient, self.patient)
        self.assertEqual(self.alert.type, 'HIGH_RISK')
        self.assertEqual(self.alert.severity, 'CRITICAL')
        self.assertIn('critical deterioration', self.alert.message)
        self.assertTrue(self.alert.is_active)
        self.assertIsNotNone(self.alert.created_at)
    
    def test_multiple_alerts_per_patient(self):
        """Test patient can have multiple alerts"""
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Temperature slightly elevated',
            severity='MEDIUM'
        )
        Alert.objects.create(
            patient=self.patient,
            type='DEVICE_OFFLINE',
            message='Monitoring device disconnected',
            severity='LOW'
        )
        alerts = Alert.objects.filter(patient=self.patient)
        self.assertEqual(alerts.count(), 3)
    
    def test_cascade_delete(self):
        """Test alerts are deleted when patient is deleted"""
        patient_id = self.patient.id
        self.patient.delete()
        self.assertFalse(Alert.objects.filter(patient_id=patient_id).exists())
    
    def test_related_name_access(self):
        """Test accessing alerts from patient"""
        alerts = self.patient.alerts.all()
        self.assertIn(self.alert, alerts)
    
    def test_alert_types(self):
        """Test all alert type choices"""
        types = ['HIGH_RISK', 'WARNING', 'DEVICE_OFFLINE']
        for alert_type in types:
            alert = Alert.objects.create(
                patient=self.patient,
                type=alert_type,
                message=f'Test {alert_type} alert',
                severity='MEDIUM'
            )
            self.assertEqual(alert.type, alert_type)
    
    def test_severity_levels(self):
        """Test all severity level choices"""
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        for severity in severities:
            alert = Alert.objects.create(
                patient=self.patient,
                type='WARNING',
                message=f'Test {severity} severity',
                severity=severity
            )
            self.assertEqual(alert.severity, severity)
    
    def test_default_is_active_true(self):
        """Test is_active defaults to True"""
        alert = Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Test alert',
            severity='LOW'
        )
        self.assertTrue(alert.is_active)
    
    def test_deactivate_alert(self):
        """Test deactivating an alert"""
        self.alert.is_active = False
        self.alert.save()
        self.alert.refresh_from_db()
        self.assertFalse(self.alert.is_active)
    
    def test_string_representation_active(self):
        """Test __str__ method for active alert"""
        result = str(self.alert)
        self.assertIn('ACTIVE', result)
        self.assertIn('HIGH_RISK', result)
        self.assertIn('John Doe', result)
        self.assertIn('CRITICAL', result)
    
    def test_string_representation_resolved(self):
        """Test __str__ method for resolved alert"""
        self.alert.is_active = False
        self.alert.save()
        result = str(self.alert)
        self.assertIn('RESOLVED', result)
    
    def test_string_representation_without_name(self):
        """Test __str__ method without patient name"""
        patient2 = Patient.objects.create(
            patient_id='PAT_999',
            bed_number='999',
            ward='General',
            hospital=self.hospital
        )
        alert = Alert.objects.create(
            patient=patient2,
            type='WARNING',
            message='Test',
            severity='LOW'
        )
        result = str(alert)
        self.assertIn('PAT_999', result)
    
    def test_alert_ordering(self):
        """Test alerts are ordered by created_at descending"""
        alert2 = Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Second alert',
            severity='MEDIUM'
        )
        
        all_alerts = list(Alert.objects.filter(patient=self.patient))
        self.assertEqual(len(all_alerts), 2)
        # Most recent should appear first
        self.assertIn(alert2, all_alerts)
        self.assertIn(self.alert, all_alerts)
    
    def test_created_at_auto_now_add(self):
        """Test created_at is set automatically and immutable"""
        original_time = self.alert.created_at
        self.alert.message = 'Updated message'
        self.alert.save()
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.created_at, original_time)
    
    def test_created_at_timezone_aware(self):
        """Test created_at is timezone aware"""
        self.assertIsNotNone(self.alert.created_at.tzinfo)
    
    def test_filter_active_alerts(self):
        """Test filtering active alerts"""
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Active warning',
            severity='MEDIUM',
            is_active=True
        )
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Resolved warning',
            severity='LOW',
            is_active=False
        )
        
        active_alerts = Alert.objects.filter(is_active=True)
        self.assertEqual(active_alerts.count(), 2)  # Including setUp alert
        
        inactive_alerts = Alert.objects.filter(is_active=False)
        self.assertEqual(inactive_alerts.count(), 1)
    
    def test_high_risk_alert(self):
        """Test creating high risk alert"""
        alert = Alert.objects.create(
            patient=self.patient,
            type='HIGH_RISK',
            message='SpO2 dropped below 85%, immediate intervention required',
            severity='CRITICAL',
            is_active=True
        )
        self.assertEqual(alert.type, 'HIGH_RISK')
        self.assertEqual(alert.severity, 'CRITICAL')
        self.assertTrue(alert.is_active)
    
    def test_device_offline_alert(self):
        """Test device offline alert"""
        alert = Alert.objects.create(
            patient=self.patient,
            type='DEVICE_OFFLINE',
            message='Bed 101 monitoring device lost connection',
            severity='HIGH',
            is_active=True
        )
        self.assertEqual(alert.type, 'DEVICE_OFFLINE')
        self.assertIn('lost connection', alert.message)
    
    def test_warning_alert(self):
        """Test warning type alert"""
        alert = Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Heart rate trending upward',
            severity='MEDIUM',
            is_active=True
        )
        self.assertEqual(alert.type, 'WARNING')
        self.assertEqual(alert.severity, 'MEDIUM')
    
    def test_multiple_patients_alerts(self):
        """Test alerts for different patients"""
        patient2 = Patient.objects.create(
            patient_id='PAT_002',
            bed_number='102',
            ward='General',
            hospital=self.hospital
        )
        alert2 = Alert.objects.create(
            patient=patient2,
            type='WARNING',
            message='Patient 2 alert',
            severity='LOW'
        )
        
        patient1_alerts = Alert.objects.filter(patient=self.patient)
        patient2_alerts = Alert.objects.filter(patient=patient2)
        
        self.assertEqual(patient1_alerts.count(), 1)
        self.assertEqual(patient2_alerts.count(), 1)
        self.assertNotEqual(patient1_alerts[0].patient, patient2_alerts[0].patient)
    
    def test_alert_message_content(self):
        """Test alert message can contain detailed information"""
        long_message = (
            "CRITICAL ALERT: Patient John Doe (PAT_001) in Bed 101, ICU ward. "
            "Multiple vital signs deteriorating: SpO2 at 82%, Heart Rate 145 BPM, "
            "Temperature 39.5°C. Immediate medical attention required."
        )
        alert = Alert.objects.create(
            patient=self.patient,
            type='HIGH_RISK',
            message=long_message,
            severity='CRITICAL'
        )
        self.assertEqual(alert.message, long_message)
        self.assertIn('CRITICAL ALERT', alert.message)
        self.assertIn('SpO2', alert.message)
    
    def test_bulk_resolve_alerts(self):
        """Test resolving multiple alerts at once"""
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Alert 1',
            severity='MEDIUM'
        )
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Alert 2',
            severity='LOW'
        )
        
        # Bulk update to resolve all alerts
        Alert.objects.filter(patient=self.patient).update(is_active=False)
        
        active_count = Alert.objects.filter(patient=self.patient, is_active=True).count()
        self.assertEqual(active_count, 0)
    
    def test_alert_history_for_patient(self):
        """Test viewing alert history for a patient"""
        # Create alerts over time
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='First warning',
            severity='LOW',
            is_active=False
        )
        Alert.objects.create(
            patient=self.patient,
            type='HIGH_RISK',
            message='Risk escalated',
            severity='HIGH',
            is_active=False
        )
        Alert.objects.create(
            patient=self.patient,
            type='WARNING',
            message='Current warning',
            severity='MEDIUM',
            is_active=True
        )
        
        all_alerts = self.patient.alerts.all()
        self.assertEqual(all_alerts.count(), 4)  # Including setUp alert
        
        resolved_alerts = self.patient.alerts.filter(is_active=False)
        self.assertEqual(resolved_alerts.count(), 2)
        
        active_alerts = self.patient.alerts.filter(is_active=True)
        self.assertEqual(active_alerts.count(), 2)

