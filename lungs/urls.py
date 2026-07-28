from django.urls import path
from . import views

app_name = 'lungs'

urlpatterns = [
    #path('', views.index, name='index'),  # or whatever your view is named
    path('predict/', views.predict_lung_disease, name='lungs_predict'),
    path('result/', views.result, name='lungs_result'),
    ]
