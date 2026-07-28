from rest_framework import serializers
from .models import PatientData, FormVitals, PredictionData, DQScore


class PatientDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientData
        fields = "__all__"


class FormVitalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormVitals
        fields = "__all__"


class PredictionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionData
        fields = "__all__"


class DQScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DQScore
        fields = "__all__"