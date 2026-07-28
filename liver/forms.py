from django import forms
from main_page.models import PatientData, FormVitals,PredictionData

class LiverPredictionForm(forms.ModelForm):
    class Meta:
        model = PredictionData
        fields = ['total_bilirubin', 'direct_bilirubin', 'alkaline_phosphotase_ALP', 
                  'alamine_aminotransferase_ALT', 'total_proteins', 'albumin','albumin_globulin_ratio','aspartate_aminotransferase_AST']
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'liver'}),
        }

class FormVitalsForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['height','weight']

class PatientDataForm(forms.ModelForm):
    class Meta:
        model = PatientData
        fields = ['age','sex']
