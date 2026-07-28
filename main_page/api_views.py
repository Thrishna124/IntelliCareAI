from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import PatientData, FormVitals, PredictionData, DQScore
from drf_spectacular.utils import extend_schema
from .serializers import (
    PatientDataSerializer,
    FormVitalsSerializer,
    PredictionDataSerializer,
    DQScoreSerializer,
)

@extend_schema(
    tags=["Patients"],
    summary="Retrieve Patient Profile",
    description="Returns the authenticated user's patient profile.",
)
class PatientListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PatientDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PatientData.objects.filter(user=self.request.user)
    
@extend_schema(
    tags=["Vitals"],
    summary="Retrieve Patient Vital Signs",
    description="Returns all recorded vital signs for the authenticated patient.",
)
class VitalListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FormVitalsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FormVitals.objects.filter(pid__user=self.request.user)
    
@extend_schema(
    tags=["Predictions"],
    summary="Retrieve Disease Predictions",
    description="""
Returns all disease prediction results generated for the authenticated patient.

Predictions may include:
- Heart Disease
- Kidney Disease
- Liver Disease
- Lung Disease
- Lung Cancer
- Diabetes
- Fitness Assessment
""",
)
class PredictionListAPIView(generics.ListCreateAPIView):
    serializer_class = PredictionDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = PatientData.objects.filter(user=self.request.user).first()

        if patient:
            return PredictionData.objects.filter(pid=patient)

        return PredictionData.objects.none()
    
@extend_schema(
    tags=["Data Quality"],
    summary="Retrieve Data Quality Scores",
    description="Returns data quality metrics associated with the authenticated patient's prediction records.",
)
class DQScoreListAPIView(generics.ListCreateAPIView):
    serializer_class = DQScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = PatientData.objects.filter(user=self.request.user).first()

        if patient:
            return DQScore.objects.filter(pid=patient)

        return DQScore.objects.none()
    
class VitalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FormVitalsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FormVitals.objects.filter(pid__user=self.request.user)
    
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(["GET"])
def api_root(request, format=None):
    return Response({
        "patients": reverse("patient-list", request=request),
        "vitals": reverse("vital-list", request=request),
        "predictions": reverse("prediction-list", request=request),
        "dqscores": reverse("dqscore-list", request=request),
        "swagger": reverse("swagger-ui", request=request),
        "schema": reverse("schema", request=request),
        "redoc": reverse("redoc", request=request),
    })