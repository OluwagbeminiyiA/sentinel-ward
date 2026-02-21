"""
AI Analysis Service using Google Gemini
Analyzes patient vitals and provides medical insights
"""
import google.generativeai as genai
from django.conf import settings
import logging
from decouple import config

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Handles AI analysis of patient vitals using Gemini"""
    
    def __init__(self):
        self.api_key = config('GEMINI_API_KEY', default='')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not configured. AI analysis will be disabled.")
    
    def analyze_vitals(self, patient, vitals):
        """
        Analyze patient vitals and provide medical insights
        
        Args:
            patient: Patient model instance
            vitals: LatestVitals model instance
            
        Returns:
            str: AI-generated analysis and recommendations
        """
        if not self.model:
            return "AI analysis unavailable - API key not configured"
        
        try:
            # Prepare patient context
            patient_context = self._prepare_patient_context(patient, vitals)
            
            # Generate analysis
            prompt = self._create_analysis_prompt(patient_context)
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error during AI analysis: {str(e)}")
            return f"AI analysis error: {str(e)}"
    
    def _prepare_patient_context(self, patient, vitals):
        """Prepare patient data for AI analysis"""
        context = {
            'patient_id': patient.patient_id,
            'patient_name': patient.name or 'Unknown',
            'bed_number': patient.bed_number,
            'ward': patient.ward,
            'temperature': float(vitals.temperature) if vitals.temperature else None,
            'heart_rate': vitals.heart_rate,
            'spo2': vitals.spo2,
            'risk_level': vitals.risk_level,
            'medical_history': patient.past_medical_records or 'No records available'
        }
        return context
    
    def _create_analysis_prompt(self, context):
        """Create prompt for Gemini AI"""
        prompt = f"""
You are a medical AI assistant analyzing patient vital signs in a hospital ward monitoring system.

Patient Information:
- Patient ID: {context['patient_id']}
- Name: {context['patient_name']}
- Location: Bed {context['bed_number']}, {context['ward']} Ward
- Medical History: {context['medical_history']}

Current Vital Signs:
- Temperature: {context['temperature']}°C (Normal: 36.5-37.5°C)
- Heart Rate: {context['heart_rate']} bpm (Normal: 60-100 bpm)
- SpO₂: {context['spo2']}% (Normal: 95-100%)
- Current Risk Assessment: {context['risk_level']}

Please provide:
1. **Clinical Assessment**: Brief analysis of the vital signs
2. **Risk Factors**: Any concerning patterns or abnormalities
3. **Recommendations**: Immediate actions or monitoring needs (max 3 points)
4. **Alert Level**: Confirm if the current risk level is appropriate

Keep the response concise (under 200 words) and clinically relevant for healthcare staff.
Format your response in clear sections with bullet points where appropriate.
"""
        return prompt
    
    def quick_risk_assessment(self, vitals):
        """
        Quick AI assessment for alert generation
        
        Args:
            vitals: LatestVitals instance
            
        Returns:
            str: Brief risk assessment for alert messages
        """
        if not self.model:
            return ""
        
        try:
            temp = float(vitals.temperature) if vitals.temperature else 0
            hr = vitals.heart_rate or 0
            spo2 = vitals.spo2 or 0
            
            prompt = f"""
Briefly assess this patient's vital signs in one sentence:
Temperature: {temp}°C, Heart Rate: {hr} bpm, SpO₂: {spo2}%

Provide only ONE concise sentence (max 20 words) describing the most critical finding.
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error during quick assessment: {str(e)}")
            return ""


# Singleton instance
_analyzer_instance = None


def get_analyzer():
    """Get or create GeminiAnalyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = GeminiAnalyzer()
    return _analyzer_instance
