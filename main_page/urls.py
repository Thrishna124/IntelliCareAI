from django.urls import path
from main_page import views
from django.http import HttpResponse

app_name = 'main_page'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('home/', views.home, name='home'),
    path('workspace/patients/', views.patient_list, name='patient_list'),
    path('workspace/patients/<int:patient_id>/select/', views.select_patient, name='select_patient'),
    
    path('update_patient_data/', views.update_patient_data, name='update_patient_data'),
    path('update_form_vitals/', views.update_form_vitals, name='update_form_vitals'),
    path('enter_form_vitals/', views.enter_form_vitals, name='enter_form_vitals'),  # Changed this line
    path('view_vital_info/', views.view_vital_info, name='view_vital_info'),
    path('enter_patient_data/', views.enter_patient_data, name='enter_patient_data'),
    path('view_prediction_data/', views.view_prediction_data, name='view_prediction_data'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/export/', views.analytics_export, name='analytics_export'),
]
