from django.urls import path
from . import views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('risk/grouped/', views.patients_by_risk, name='patients_by_risk'),
]
