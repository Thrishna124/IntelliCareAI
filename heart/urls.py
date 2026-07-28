from django.urls import path
from . import views

app_name = 'heart'

urlpatterns = [
    path('predict/', views.predict_heart_disease, name='predict_heart_disease'),
    path('result/', views.result, name='heart_result'),
    ]
