from django import forms
from main_page.models import PatientData, FormVitals,PredictionData

class LungCancerPredictionForm(forms.ModelForm):
    class Meta:
        model = PredictionData
        fields = ['image']
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'lung_cancer'}),
        }

class FormVitalsForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['height','weight']

class PatientDataForm(forms.ModelForm):
    class Meta:
        model = PatientData
        fields = ['age','sex']
