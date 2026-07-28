from django import forms
from main_page.models import PatientData,FormVitals,PredictionData

class FitnessForm(forms.ModelForm):
    total_steps = forms.IntegerField(required=True)
    calories_burned = forms.FloatField(required=True)
    class Meta:
        model = PredictionData
        fields = ['total_steps','calories_burned']
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'fitness'}),
        }


class PatientDataForm(forms.ModelForm):
    class Meta:
        model = PatientData
        fields = ['age','sex','lifestyle']  # Specify fields from PatientData

class FormVitalsForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['height', 'weight','BMI'] 