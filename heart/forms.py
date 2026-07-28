from django import forms
from main_page.models import PatientData,PredictionData

from predictions.forms import StyledPredictionForm

class HeartPredictionForm(StyledPredictionForm):    
    
    FASTING_BLOOD_SUGAR_CHOICES = [
        ('0', '<= 120 mg/dl'),
        ('1', '> 120 mg/dl')
    ]
    
    fastingbloodsugar = forms.ChoiceField(
        choices=FASTING_BLOOD_SUGAR_CHOICES,
        widget=forms.RadioSelect,  # Optional: Use a radio button selection
        required=True,
        label="fasting blood sugar"
    )
    CHEST_PAIN_CHOICES = [
        ('0','typical angina'),
        ('1','atypical angina'),
        ('2','non-anginal pain'), 
        ('3','asymptomatic')
    ]
    chestpain = forms.ChoiceField(
        choices=CHEST_PAIN_CHOICES,
        widget=forms.RadioSelect,  # Optional: Use a radio button selection
        required=True,
        label="chest pain"
    )

    ANGIA_CHOICES = [
        ('0','no'),
        ('1','yes')
    ]
    exerciseangia = forms.ChoiceField(
        choices= ANGIA_CHOICES,
        widget=forms.RadioSelect,  # Optional: Use a radio button selection
        required=True,
        label= 'Exercise induced angina'
    )

    SLOPE_CHOICES = [
        ('1','upsloping'),
        ('2','flat'), 
        ('3','downsloping')
    ]

    slope = forms.ChoiceField(
        choices= SLOPE_CHOICES,
        widget=forms.RadioSelect,  # Optional: Use a radio button selection
        required=True,
        label= 'slope'
    )

    NO_OF_MAJOR_VALVES_CHOICES = [
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    ]

    noofmajorvessels = forms.ChoiceField(
        choices=NO_OF_MAJOR_VALVES_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Number of Major Valves"
    )
    RESTING_ELECTRO_CHOICES = [
        ('0','normal'), 
        ('1','ST-T wave abnormality'), 
        ('2','probable or definite left ventricular hypertrophy')
    ]
    
    restingrelectro = forms.ChoiceField(
        choices=RESTING_ELECTRO_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Resting electrocardiogram"
    )
    class Meta:
        model = PredictionData
        fields = ['chestpain', 'restingBP',
            'cholesterol', 'fastingbloodsugar', 'restingrelectro',
            'maxheartrate', 'exerciseangia', 'oldpeak', 'slope',
            'noofmajorvessels']
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'heart'}),
        }

class PatientDataForm(StyledPredictionForm):   
    class Meta:
        model = PatientData
        fields = ['age','sex']

