from django import forms
from main_page.models import PatientData, FormVitals,PredictionData

class DiabetesPredictionForm(forms.ModelForm):
    class Meta:
        model = PredictionData
        fields = ['urea', 'creatinine', 'hba1c', 
                  'cholesterol', 'triglycerides', 'HDL','LDL','VLDL']
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'pancreas'}),
        }

class FormVitalsForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['height','weight']

class PatientDataForm(forms.ModelForm):
    class Meta:
        model = PatientData
        fields = ['age','sex']

