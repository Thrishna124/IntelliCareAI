from django.urls import path
from . import views

app_name = 'pancreas'

urlpatterns = [
    #path('', views.index, name='index'),  # or whatever your view is named
    path('predict/', views.predict_diabetes, name='diabetes_predict'),
    path('result/', views.result, name='diabetes_result'),
    ]
