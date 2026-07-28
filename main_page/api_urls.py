from django.urls import path
from . import api_views
from .api_views import (
    PatientListCreateAPIView,
    VitalListCreateAPIView,
    VitalDetailAPIView,
    PredictionListAPIView,
    DQScoreListAPIView,
    api_root,
)

urlpatterns = [

    path("", api_root, name="api-root"),

    path("patients/", PatientListCreateAPIView.as_view(), name="patient-list"),

    path("vitals/", VitalListCreateAPIView.as_view(), name="vital-list"),

    path("vitals/<int:pk>/", VitalDetailAPIView.as_view(), name="vital-detail"),

    path("predictions/", PredictionListAPIView.as_view(), name="prediction-list"),

    path("dqscores/", DQScoreListAPIView.as_view(), name="dqscore-list"),
]