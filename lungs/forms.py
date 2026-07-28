from django import forms
from main_page.models import PatientData, FormVitals,PredictionData

class LungsPredictionForm(forms.ModelForm):
    class Meta:
        model = PredictionData
        fields = ["predicted_FEV1",
            "predicted_VC",
            "actual_FEV1",
            "actual_VC",
            "fev1_vc_ratio",]
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'lungs'}),
        }

class FormVitalsForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['height','weight']

class PatientDataForm(forms.ModelForm):
    class Meta:
        model = PatientData
        fields = ['age','sex']
