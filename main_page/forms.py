from django import forms
from .models import PatientData,FormVitals,PredictionData
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import date
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm,UserCreationForm

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    # Customize the form fields
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class PatientDataForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly active (light exercise 1-3 days/week)'),
        ('moderate', 'Moderately active (moderate exercise 3-5 days/week)'),
        ('active', 'Very active (hard exercise 6-7 days/week)'),
        ('super_active', 'Super active (very hard exercise/physical job)'),
    ]
    
    DOB = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d', attrs={ 'type': 'date', 'class': 'form-control', 'placeholder': 'Date of Birth' }))
    #date = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker'}))
    phone_cell = forms.CharField(
        validators=[RegexValidator(regex=r'^\d{10}$', message='Phone number must be exactly 10 digits.')]
    )
    sex = forms.ChoiceField(choices=GENDER_CHOICES,required=True)
    lifestyle = forms.ChoiceField(choices=ACTIVITY_LEVEL_CHOICES,required=True)
    pid = forms.CharField(required=False)
    fname = forms.CharField(label="First Name")
    mname = forms.CharField(label="Middle Name",required=False)
    lname = forms.CharField(label="Last Name")
    age = forms.IntegerField(required=True)

    class Meta:
        model = PatientData
        fields = ['pid', 'fname', 'mname', 'lname', 'age','DOB','sex','address','city','state','country_code',
                  'pincode','phone_cell','lifestyle']

    def clean_pid(self):
        pid = self.cleaned_data.get('pid')
        if PatientData.objects.filter(pid=pid).exists():
            raise forms.ValidationError("A patient with this PID already exists.")
        return pid
    
    def clean_DOB(self):
        dob = self.cleaned_data.get('DOB')
        if dob > timezone.now().date():
            raise ValidationError("Date of Birth cannot be in the future.")
        return dob

    # Form-level validation for combined logic: Ensure age is consistent with DOB
    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get('DOB')
        age = cleaned_data.get('age')

        if dob and age:
            today = date.today()
            calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if calculated_age != age:
                raise ValidationError(f"Age does not match with the Date of Birth. Calculated age is {calculated_age}.")
        return cleaned_data

def calculate_bmi(weight, height):
    if height != 0:  # Ensure height is not zero to avoid division by zero
        height_m = height / 100  # Convert height from cm to meters
        bmi = weight / (height_m ** 2)  # BMI formula
        return round(bmi, 2)
    return None  # Return None if height is zero

def calculate_bmi_status(bmi):
            if bmi < 18.5:
                bmi_status= "Under Weight"
            elif 18.5 <= bmi < 24.9:
                bmi_status = "Healthy Weight"
            elif 25 <= bmi < 29.9:
                bmi_status = "Over Weight"
            else:
                bmi_status = "Obese"
            return bmi_status


class VitalDetailsForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['weight','height','heart_rate','temperature','respiration_rate']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Calculate BMI and BMI status
        instance.BMI = calculate_bmi(instance.weight, instance.height)
        instance.BMI_status = calculate_bmi_status(instance.BMI)
        
        if commit:
            instance.save()
        return instance


class PatientDataUpdateForm(forms.ModelForm):
    class Meta:
        model = PatientData
        fields = ['address', 'city', 'state', 'country_code', 'pincode', 'phone_cell', 'lifestyle','DOB']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

class VitalDetailsUpdateForm(forms.ModelForm):
    class Meta:
        model = FormVitals
        fields = ['weight', 'heart_rate', 'temperature', 'respiration_rate']

    
class PredictionDataForm(forms.ModelForm):
    class Meta:
        model = PredictionData
        fields = ['urea','creatinine','hba1c','cholesterol','triglycerides','HDL','LDL','VLDL',
                  'chestpain','restingBP','fastingbloodsugar','restingrelectro','maxheartrate','exerciseangia','oldpeak','slope','noofmajorvessels',
                  'total_bilirubin','direct_bilirubin','alkaline_phosphotase_ALP','alamine_aminotransferase_ALT','total_proteins','albumin','albumin_globulin_ratio','aspartate_aminotransferase_AST',
                  'bp','sg','al','su','rbc','pc','pcc','ba','bgr','bu','sc','sod','pot','hemo','pcv','wc','rc','htn','dm','cad','appet','pe','ane']