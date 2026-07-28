from django import forms
from main_page.models import PredictionData,PatientData,FormVitals

#numeric_features = ['age', 'bp', 'bgr', 'bu', 'sc', 'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc']
#categorical_features = ['sg','al', 'su', 'rbc', 'pc', 'pcc', 'ba', 'htn', 'dm', 'cad', 'appet', 'pe', 'ane']
class KidneyPredictionForm(forms.ModelForm):
    NORMAL_CHOICES = [('normal','normal'), ('abnormal','abnormal')]
    PRESENT_CHOICES = [('present','present'), ('notpresent','not present')]
    YES_CHOICES = [('yes','yes'), ('no','no')]
    GOOD_CHOICES = [('good','good'), ('poor','poor')]
    SG_CHOICES = [('1','1.005'), ('2','1.010'),('3','1.015'),('4','1.020'),('5','1.025')]
    AL_CHOICES = [('0','Normal - 0 mg/dL'),('1','Trace - 0 to 10 mg/dL'),('2','Mild - 10 to 30 mg/dL'),('3','Moderate - 30 to 100 mg/dL'),
                  ('4','severe - 100 to 300 mg/dL'),('5','very severe -  Greater than 300 mg/dL')]
    SU_CHOICES = [('0','None - 0 mg/dL'),('1','Trace - 0 to 100 mg/dL'),('2','Mild - 100 to 250 mg/dL'),('3','Moderate - 250 to 500 mg/dL'),
                ('4','Severe - 500 to 1000 mg/dL'),('5','Very severe - Greater than 1000 mg/dL')]
    
    al = forms.ChoiceField(choices= AL_CHOICES,
                            widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
                            required=True,  # Set to True if the field is mandatory
                            label="Albumin") 
    
    su = forms.ChoiceField(choices= SU_CHOICES,
                            widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
                            required=True,  # Set to True if the field is mandatory
                            label="Sugar level") 
    
    sg = forms.ChoiceField(choices= SG_CHOICES,
                            widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
                            required=True,  # Set to True if the field is mandatory
                            label="Specific Gravity Mapping")    
    rbc = forms.ChoiceField(
        choices=NORMAL_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Red Blood Cells"
    )
    pc = forms.ChoiceField(
        choices=NORMAL_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Protein Creatinine Ratio"
    )
    pcc = forms.ChoiceField(
        choices=PRESENT_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Pheochromocytoma"
    )
    ba = forms.ChoiceField(
        choices=PRESENT_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Presence of bacteria"
    )
    htn = forms.ChoiceField(
        choices=YES_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Hypertension"
    )
    dm = forms.ChoiceField( 
        choices=YES_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Diabetes Mellitus"
    )
    cad = forms.ChoiceField(
        choices=YES_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Coronary Artery Disease"
    )
    appet = forms.ChoiceField(
        choices=GOOD_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Appetite"
    )
    pe = forms.ChoiceField(
        choices=YES_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Swollen Feet"
    )
    ane = forms.ChoiceField(
        choices=YES_CHOICES,
        widget=forms.Select,  # Use Select widget for dropdown, or RadioSelect for radio buttons
        required=True,  # Set to True if the field is mandatory
        label="Anemia"
    )
    bp = forms.FloatField(
        required=True,  # Use required=True if the field is mandatory
        label="Blood Pressure (in mmHg)",
        widget=forms.NumberInput(attrs={'placeholder': 'Blood Pressure in mmHg'})
    )

    bgr = forms.IntegerField(
        required=True,
        label="Blood Glucose Random (in mg/dl)",
        widget=forms.NumberInput(attrs={'placeholder': 'Random Blood Glucose level'})
    )
    bu = forms.IntegerField(
        required=True,
        label="Blood Urea (in mg/dl)",
        widget=forms.NumberInput(attrs={'placeholder': 'Blood Urea level'})
    )
    sc = forms.FloatField(
        required=True,
        label="Serum Creatinine (in mg/dl)",
        widget=forms.NumberInput(attrs={'placeholder': 'Serum Creatinine level'})
    )
    sod = forms.IntegerField(
        required=True,
        label="Sodium (in mEq/L)",
        widget=forms.NumberInput(attrs={'placeholder': 'Sodium level'})
    )
    pot = forms.FloatField(
        required=True,
        label="Potassium (in mEq/L)",
        widget=forms.NumberInput(attrs={'placeholder': 'Potassium level'})
    )
    hemo = forms.FloatField(
        required=True,
        label="Hemoglobin (in g/dl)",
        widget=forms.NumberInput(attrs={'placeholder': 'Hemoglobin level'})
    )
    pcv = forms.IntegerField(
        required=True,
        label="Packed Cell Volume",
        widget=forms.NumberInput(attrs={'placeholder': 'Packed Cell volume'})
    )
    wc = forms.IntegerField(
        required=True,
        label="White Blood Cell Count (in cells/cumm)",
        widget=forms.NumberInput(attrs={'placeholder': 'White Blood Cell count'})
    )
    rc = forms.FloatField(
        required=True,
        label="Red Blood Cell Count (in millions/cmm)",
        widget=forms.NumberInput(attrs={'placeholder': 'Red Blood Cell count'})
    )

    class Meta:
        model = PredictionData
        fields = ['bp', 'sg','al', 'bu', 'rbc','pc','pcc','ba','bgr', 'sc', 'sod', 'pot','hemo','pcv','wc',
                  'rc','htn','dm','cad', 'appet','pe','ane']
        widgets = {
            'prediction_type': forms.HiddenInput(attrs={'value': 'kidney'}),
        }

    class PatientDataForm(forms.ModelForm):
        class Meta:
            model = PatientData
            fields = ['age','sex']

    class FormVitalsForm(forms.ModelForm):
        class Meta:
            model = FormVitals
            fields = ['height','weight']