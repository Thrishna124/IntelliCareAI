from django.urls import path
from . import views

app_name = 'liver'

urlpatterns = [
    #path('', views.index, name='index'),  # or whatever your view is named
    path('predict/', views.predict_liver_disease, name='liver_predict'),
    path('result/', views.result, name='liver_result'),
    ]
