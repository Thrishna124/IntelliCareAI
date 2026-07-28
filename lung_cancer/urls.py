from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'lung_cancer'

urlpatterns = [
    #path('', views.index, name='index'),  # or whatever your view is named
    path('predict/', views.predict_lung_cancer, name='lung_cancer_predict'),
    path('result/<int:pk>/', views.result, name='lung_cancer_result'),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

