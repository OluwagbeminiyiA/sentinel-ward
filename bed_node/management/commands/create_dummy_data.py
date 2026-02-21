"""
Django management command to populate database with dummy data for frontend development.

Usage:
    python manage.py create_dummy_data
    python manage.py create_dummy_data --clear  # Clear existing data first
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta

from bed_node.models import Device, LatestVitals, Alert, Prediction
from patients.models import Patient
from hospitals.models import Hospital


class Command(BaseCommand):
    help = 'Creates dummy data for frontend development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new dummy data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Alert.objects.all().delete()
            LatestVitals.objects.all().delete()
            Prediction.objects.all().delete()
            Device.objects.all().delete()
            Patient.objects.all().delete()
            Hospital.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Existing data cleared'))

        self.stdout.write(self.style.SUCCESS('Creating dummy data...'))
        
        with transaction.atomic():
            # Create hospitals
            hospitals = self._create_hospitals()
            
            # Create patients with various conditions
            patients = self._create_patients(hospitals)
            
            # Create devices for each bed
            devices = self._create_devices(patients)
            
            # Create vitals for each patient
            vitals = self._create_vitals(patients)
            
            # Create alerts for some patients
            alerts = self._create_alerts(patients, vitals)
            
            # Create predictions for some patients
            predictions = self._create_predictions(patients)

        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {len(hospitals)} hospitals'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(patients)} patients'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(devices)} devices'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(vitals)} vitals records'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(alerts)} alerts'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(predictions)} predictions'))
        self.stdout.write(self.style.SUCCESS('\n🎉 Dummy data created successfully!'))
        self.stdout.write(self.style.WARNING('\nAPI Endpoints to test:'))
        self.stdout.write('  GET  /api/patients/')
        self.stdout.write('  GET  /api/patients/<patient_id>/')
        self.stdout.write('  GET  /api/bed-node/dashboard/')
        self.stdout.write('  GET  /api/bed-node/alerts/')
        self.stdout.write('  POST /api/bed-node/simulate-vitals/')

    def _create_hospitals(self):
        """Create sample hospitals"""
        hospitals = [
            Hospital.objects.create(name='Central City Hospital'),
            Hospital.objects.create(name='St. Mary Medical Center'),
        ]
        return hospitals

    def _create_patients(self, hospitals):
        """Create diverse patient profiles"""
        patients_data = [
            # Critical patients
            {
                'patient_id': 'PAT001',
                'name': 'John Smith (68M)',
                'bed_number': '101',
                'ward': 'ICU',
                'past_medical_records': 'Age 68. Hypertension, Type 2 Diabetes, CAD with previous MI 2019. Recent pneumonia. Admitted 3 days ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT002',
                'name': 'Maria Garcia (54F)',
                'bed_number': '102',
                'ward': 'ICU',
                'past_medical_records': 'Age 54. COPD, CHF, Atrial Fibrillation. Admitted with acute exacerbation 5 days ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT003',
                'name': 'Robert Johnson (72M)',
                'bed_number': '103',
                'ward': 'ICU',
                'past_medical_records': 'Age 72. Septic shock, multi-organ dysfunction. History of chronic kidney disease. Admitted 2 days ago.',
                'hospital': hospitals[0]
            },
            # High-risk patients
            {
                'patient_id': 'PAT004',
                'name': 'Linda Davis (61F)',
                'bed_number': '201',
                'ward': 'Medical Ward',
                'past_medical_records': 'Age 61. Post-operative day 2 from cardiac surgery. Hypertension, hyperlipidemia. Admitted 4 days ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT005',
                'name': 'James Wilson (45M)',
                'bed_number': '202',
                'ward': 'Medical Ward',
                'past_medical_records': 'Age 45. Cellulitis of lower leg, Type 1 Diabetes. Poor glycemic control. Admitted 6 days ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT006',
                'name': 'Patricia Martinez (58F)',
                'bed_number': '203',
                'ward': 'Medical Ward',
                'past_medical_records': 'Age 58. Chest pain, rule out MI. Smoker, family history of CAD. Admitted 1 day ago.',
                'hospital': hospitals[0]
            },
            # Stable patients
            {
                'patient_id': 'PAT007',
                'name': 'Michael Brown (35M)',
                'bed_number': '301',
                'ward': 'Medical Ward',
                'past_medical_records': 'Age 35. Appendectomy, recovering well. No significant medical history. Admitted 2 days ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT008',
                'name': 'Sarah Anderson (42F)',
                'bed_number': '302',
                'ward': 'Surgical Ward',
                'past_medical_records': 'Age 42. Cholecystectomy. Mild asthma, well controlled. Admitted 3 days ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT009',
                'name': 'David Lee (29M)',
                'bed_number': '303',
                'ward': 'Surgical Ward',
                'past_medical_records': 'Age 29. Knee arthroscopy. Active, healthy individual. Admitted 1 day ago.',
                'hospital': hospitals[0]
            },
            {
                'patient_id': 'PAT010',
                'name': 'Jennifer Taylor (51F)',
                'bed_number': '304',
                'ward': 'Medical Ward',
                'past_medical_records': 'Age 51. Pneumonia, responding to antibiotics. History of asthma. Admitted 4 days ago.',
                'hospital': hospitals[0]
            },
            # Additional patients at second hospital
            {
                'patient_id': 'PAT011',
                'name': 'Christopher White (66M)',
                'bed_number': '101',
                'ward': 'ICU',
                'past_medical_records': 'Age 66. Stroke, left sided weakness. Hypertension, diabetes. Admitted 7 days ago.',
                'hospital': hospitals[1]
            },
            {
                'patient_id': 'PAT012',
                'name': 'Nancy Thompson (49F)',
                'bed_number': '201',
                'ward': 'Medical Ward',
                'past_medical_records': 'Age 49. Gastroenteritis, dehydration. Otherwise healthy. Admitted 2 days ago.',
                'hospital': hospitals[1]
            },
        ]

        patients = []
        for data in patients_data:
            patient = Patient.objects.create(**data)
            patients.append(patient)
        
        return patients

    def _create_devices(self, patients):
        """Create IoT devices for each patient bed"""
        devices = []
        for patient in patients:
            # Use hospital ID to make device_id unique across hospitals
            hospital_code = 'CCH' if 'Central' in patient.hospital.name else 'SMM'
            device = Device.objects.create(
                device_id=f'{hospital_code}_bed_{patient.bed_number}_node',
                bed_number=patient.bed_number,
                status=random.choice(['ONLINE', 'ONLINE', 'ONLINE', 'OFFLINE'])  # 75% online
            )
            devices.append(device)
        return devices

    def _create_vitals(self, patients):
        """Create vital signs with varying risk levels"""
        vitals_configs = {
            'CRITICAL': {
                'temp_range': (38.5, 40.5),
                'hr_range': (110, 145),
                'spo2_range': (85, 92),
                'ai_analysis': [
                    'CRITICAL: Multiple concerning parameters detected. Patient shows severe fever ({}°C), tachycardia ({} BPM), and hypoxemia (SpO2 {}%). This constellation suggests possible sepsis or severe respiratory compromise. IMMEDIATE physician evaluation required. Recommend: 1) Oxygen supplementation to maintain SpO2 >94%, 2) Blood cultures, CBC, lactate, 3) Early broad-spectrum antibiotics if infection suspected, 4) Fluid resuscitation, 5) Consider ICU transfer if not already in ICU. Close monitoring of vital signs and mental status essential.',
                    'SEVERE: Patient critically unstable with temperature {}°C, heart rate {} BPM, oxygen saturation {}%. High suspicion for septic shock or acute respiratory distress. Urgent interventions needed: establish IV access, draw blood cultures, initiate sepsis protocol. Consider invasive ventilation if respiratory status deteriorates. Monitor for signs of multi-organ dysfunction.',
                    'CRITICAL ALERT: Hemodynamic instability evident. Temperature {}°C indicates severe infection, HR {} BPM suggests compensatory tachycardia or arrhythmia, SpO2 {}% indicates severe hypoxemia. Patient may be progressing to septic shock. Immediate assessment required. Activate rapid response team. Prepare for potential ICU transfer and invasive monitoring.',
                ]
            },
            'HIGH': {
                'temp_range': (37.8, 38.4),
                'hr_range': (95, 109),
                'spo2_range': (93, 94),
                'ai_analysis': [
                    'HIGH RISK: Patient showing elevated temperature ({}°C), increased heart rate ({} BPM), and borderline low oxygen saturation ({}%). These findings warrant close monitoring. Recommend: 1) Repeat vitals in 1-2 hours, 2) Assess for infection source, 3) Consider supplemental oxygen, 4) Review medication regimen, 5) Monitor fluid status. Early intervention may prevent deterioration.',
                    'CONCERNING: Vitals trending toward abnormal range. Temperature {}°C, HR {} BPM, SpO2 {}%. Given patient medical history, increased monitoring frequency recommended. Consider chest X-ray, urinalysis, blood work if not recently done. Ensure adequate hydration and pain control.',
                    'ELEVATED RISK: Temperature {}°C with heart rate {} BPM and SpO2 {}% indicate patient requires attention. May be early signs of infection or clinical deterioration. Recommend thorough physical examination, vital signs every 2-4 hours, and proactive management to prevent escalation.',
                ]
            },
            'MEDIUM': {
                'temp_range': (37.2, 37.7),
                'hr_range': (80, 94),
                'spo2_range': (95, 96),
                'ai_analysis': [
                    'MODERATE: Patient vitals slightly outside optimal range. Temperature {}°C, heart rate {} BPM, SpO2 {}%. Continue current monitoring schedule. Ensure patient comfort and adequate hydration. These values may be within normal variation but warrant continued observation.',
                    'MILD CONCERN: Vitals showing minor variations. Temp {}°C, HR {} BPM, SpO2 {}%. No immediate intervention required but maintain vigilance. Document any symptoms or patient complaints. Routine monitoring adequate at this time.',
                    'STABLE WITH MONITORING: Current readings (Temp: {}°C, HR: {} BPM, SpO2: {}%) are borderline but not immediately concerning. Continue standard care protocols. Reassess if patient develops new symptoms or if vitals trend negatively.',
                ]
            },
            'LOW': {
                'temp_range': (36.5, 37.1),
                'hr_range': (60, 79),
                'spo2_range': (97, 100),
                'ai_analysis': [
                    'STABLE: Patient vitals within normal limits. Temperature {}°C, heart rate {} BPM, oxygen saturation {}%. Continue routine monitoring as per protocol. Patient appears stable with no immediate concerns. Maintain current treatment plan.',
                    'NORMAL: All vital signs within acceptable ranges. Temp {}°C, HR {} BPM, SpO2 {}%. Patient hemodynamically stable. Continue standard care. Routine vital sign checks adequate.',
                    'OPTIMAL: Excellent vital signs - Temperature {}°C, heart rate {} BPM, SpO2 {}%. Patient showing good response to treatment. Continue current management. Standard monitoring intervals appropriate.',
                ]
            }
        }

        vitals = []
        for i, patient in enumerate(patients):
            # Assign risk levels based on patient position (ICU patients more critical)
            if patient.ward == 'ICU':
                risk_level = random.choice(['CRITICAL', 'CRITICAL', 'HIGH', 'HIGH', 'MEDIUM'])
            elif 'post-operative' in patient.past_medical_records.lower() or 'surgery' in patient.past_medical_records.lower():
                risk_level = random.choice(['HIGH', 'HIGH', 'MEDIUM', 'MEDIUM', 'LOW'])
            else:
                risk_level = random.choice(['MEDIUM', 'MEDIUM', 'LOW', 'LOW', 'LOW'])

            config = vitals_configs[risk_level]
            temp = round(random.uniform(*config['temp_range']), 1)
            hr = random.randint(*config['hr_range'])
            spo2 = random.randint(*config['spo2_range'])
            
            # Generate AI analysis
            ai_template = random.choice(config['ai_analysis'])
            ai_analysis = ai_template.format(temp, hr, spo2)

            vital = LatestVitals.objects.create(
                patient=patient,
                temperature=Decimal(str(temp)),
                heart_rate=hr,
                spo2=spo2,
                risk_level=risk_level,
                ai_analysis=ai_analysis
            )
            vitals.append(vital)
        
        return vitals

    def _create_alerts(self, patients, vitals):
        """Create alerts for critical and high-risk patients"""
        alerts = []
        
        for vital in vitals:
            if vital.risk_level in ['CRITICAL', 'HIGH']:
                # Create multiple alerts for critical patients
                alert_count = 2 if vital.risk_level == 'CRITICAL' else 1
                
                for _ in range(alert_count):
                    alert_type = 'HIGH_RISK' if vital.risk_level == 'CRITICAL' else 'WARNING'
                    severity = random.choice(['CRITICAL', 'HIGH']) if vital.risk_level == 'CRITICAL' else 'MEDIUM'
                    
                    # Create specific alert messages
                    messages = []
                    if vital.temperature and vital.temperature >= 38.5:
                        messages.append(f'High temperature: {vital.temperature}°C')
                    if vital.heart_rate and vital.heart_rate >= 110:
                        messages.append(f'Tachycardia: {vital.heart_rate} BPM')
                    if vital.spo2 and vital.spo2 <= 93:
                        messages.append(f'Low oxygen: {vital.spo2}%')
                    
                    if not messages:
                        messages.append('Abnormal vital signs detected')
                    
                    alert = Alert.objects.create(
                        patient=vital.patient,
                        type=alert_type,
                        message=' | '.join(messages),
                        severity=severity,
                        ai_analysis=vital.ai_analysis,
                        is_active=True
                    )
                    alerts.append(alert)
        
        # Add some device offline alerts
        offline_devices = Device.objects.filter(status='OFFLINE')
        for device in offline_devices:
            try:
                # Extract hospital code from device_id to find the correct patient
                hospital_code = device.device_id.split('_')[0]
                hospital_name = 'Central City Hospital' if hospital_code == 'CCH' else 'St. Mary Medical Center'
                hospital = Hospital.objects.get(name=hospital_name)
                patient = Patient.objects.get(bed_number=device.bed_number, hospital=hospital)
                alert = Alert.objects.create(
                    patient=patient,
                    type='DEVICE_OFFLINE',
                    message=f'Monitoring device {device.device_id} is offline - bed {device.bed_number}',
                    severity='HIGH',
                    ai_analysis='Device connectivity lost. Patient monitoring may be compromised. Ensure manual vital signs checks are performed according to protocol. Technical support has been notified.',
                    is_active=True
                )
                alerts.append(alert)
            except (Patient.DoesNotExist, Hospital.DoesNotExist):
                pass
        
        return alerts

    def _create_predictions(self, patients):
        """Create AI predictions for some patients"""
        predictions = []
        
        # Create predictions for high-risk patients
        high_risk_patients = [p for p in patients if p.ward == 'ICU' or 'septic' in p.past_medical_records.lower()]
        
        risk_levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        confidence_ranges = {
            'CRITICAL': (85, 98),
            'HIGH': (75, 92),
            'MEDIUM': (60, 80),
            'LOW': (65, 85)
        }
        
        drivers_templates = {
            'CRITICAL': 'Severe vital sign abnormalities, multiple organ involvement, history of chronic conditions, recent deterioration',
            'HIGH': 'Elevated temperature and heart rate, concerning SpO2 levels, underlying comorbidities',
            'MEDIUM': 'Mild vital sign variations, post-operative status, requires monitoring',
            'LOW': 'Stable vitals, good response to treatment, minimal risk factors'
        }
        
        for patient in high_risk_patients[:8]:  # Create predictions for 8 patients
            risk_level = random.choice(risk_levels)
            confidence = round(random.uniform(*confidence_ranges[risk_level]), 2)
            
            prediction = Prediction.objects.create(
                patient=patient,
                risk_level=risk_level,
                confidence=Decimal(str(confidence)),
                drivers=drivers_templates[risk_level]
            )
            predictions.append(prediction)
        
        return predictions
