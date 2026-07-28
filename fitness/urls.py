from django.urls import path
from . import views

app_name = 'fitness'

urlpatterns = [
    path('predict/', views.fitness_calculator, name='fitness_predict'),
    path('result/', views.result, name='fitness_result'),
    ]
