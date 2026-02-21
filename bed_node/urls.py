from django.urls import path
from . import views

urlpatterns = [
    # IoT device endpoints
    path('vitals/receive/', views.receive_vitals, name='receive_vitals'),
    path('vitals/simulate/', views.simulate_vitals, name='simulate_vitals'),
    path('device/status/', views.update_device_status, name='update_device_status'),
    
    # Patient vitals
    path('patients/<str:patient_id>/vitals/', views.get_patient_vitals, name='get_patient_vitals'),
    
    # Alerts
    path('alerts/', views.get_all_alerts, name='get_all_alerts'),
    path('patients/<str:patient_id>/alerts/', views.get_patient_alerts, name='get_patient_alerts'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Devices
    path('devices/', views.get_devices, name='get_devices'),
]
