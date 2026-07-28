from django.urls import path
from . import views

app_name = 'kidney'

urlpatterns = [
    #path('', views.index, name='index'),  # or whatever your view is named
    path('predict/', views.predict_kidney_disease, name='kidney_predict'),
    path('result/', views.result, name='kidney_result'),
    ]
