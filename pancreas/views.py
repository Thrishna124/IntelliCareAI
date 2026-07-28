########### Import Statements ##########

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from pancreas.forms import DiabetesPredictionForm

from main_page.models import (
    PatientData,
    PredictionData,
    FormVitals
)

from main_page.utils.prediction_utils import (
    save_dq_score,
)
from main_page.utils.clinical_workspace import get_active_patient

from django.db import transaction

logger = logging.getLogger(__name__)


############ Model Paths ############

MODEL_DIR = Path(__file__).resolve().parent / "models"


@lru_cache(maxsize=1)
def get_prediction_model():
    return joblib.load(MODEL_DIR / "diabetes_prediction_model.pkl")


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(MODEL_DIR / "diabetes_diagnosis_model.pkl")


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(MODEL_DIR / "diabetes_preprocessor.pkl")

NUMERIC_FEATURES = [
    "age",
    "urea",
    "creatinine",
    "hba1c",
    "cholesterol",
    "triglycerides",
    "HDL",
    "LDL",
    "VLDL",
    "BMI",
]

CATEGORICAL_FEATURES = [
    "sex"
]

############ Data Processing ############

def process_diabetes_data(data):
    """
    Prepare diabetes prediction input for the trained preprocessor.
    """
    # Convert the input data (which is likely a dictionary) to a DataFrame
    
    # The prediction input represents one selected patient, so construct one row.
    # Passing a scalar dictionary directly raises a pandas ValueError.
    df = pd.DataFrame([data])

    expected_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES

    # Ensure every expected feature exists
    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.NA

    # Arrange columns in training order
    df = df[expected_columns]

    # Replace missing values
    df = df.fillna(0)

    logger.debug("Diabetes prediction input:\n%s", df)

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


################ Prediction View ################

@login_required
def predict_diabetes(request):
    # Fetch the patient data from PatientData and FormVitals tables
    patient_data = get_active_patient(request)

    if patient_data is None:
        return render(
            request,
            "prediction/pancreas/predict.html",
            {
                "form": DiabetesPredictionForm(),
                "error": "Select a patient from the Clinical Workspace before starting a prediction."
            },
        )
    vitals_data = FormVitals.objects.filter(pid=patient_data).first()

    if vitals_data is None:
        return render(
            request,
            "prediction/pancreas/predict.html",
            {
                "form": DiabetesPredictionForm(),
                "error": "Patient vitals are required before prediction."
            },
        )
    
    logger.debug(f"Vitals Data: {vitals_data}")  # Ensure vitals_data is correctly populated

    if request.method == 'POST':
        form = DiabetesPredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Prepare data for prediction
            data_for_prediction = {
                'age': patient_data.age,
                'sex': 'M' if patient_data.sex == 'Male' else 'F',
                'BMI': vitals_data.BMI,
                'urea': data['urea'],
                'creatinine': data['creatinine'],
                'hba1c': data['hba1c'],
                'cholesterol': data['cholesterol'],
                'triglycerides': data['triglycerides'],
                'HDL': data['HDL'],
                'LDL': data['LDL'],
                'VLDL': data['VLDL']
            }
            
            try:
                input_data = process_diabetes_data(data_for_prediction)

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                prediction = prediction_model.predict(input_data)
                diagnosis = diagnosis_model.predict(input_data)
                # Save data to the PredictionData table
                prediction_result = PredictionData(
                    urea=data['urea'],
                    creatinine=data['creatinine'],
                    hba1c=data['hba1c'],
                    cholesterol=data['cholesterol'],
                    triglycerides=data['triglycerides'],
                    HDL=data['HDL'],
                    LDL=data['LDL'],
                    VLDL=data['VLDL'],
                    prediction="Yes" if prediction[0] == 1 else "No",
                    prediction_type='pancreas',
                    diagnosis=diagnosis[0],
                    pid=patient_data
                )

                with transaction.atomic():
                    prediction_result.save()

                    pancreas_dq_score = save_dq_score(
                    prediction_type="pancreas",
                    patient=patient_data,
                    prediction_data=data_for_prediction,
                )

                try:
                    prediction_result.save()
                    pancreas_dq_score.save()
                except Exception:
                    logger.exception("Unable to save prediction.")
                    raise

         # Render the result page with the prediction and diagnosis
                return render(request, 'pancreas/result.html', {
                        'patient': patient_data,
                        'vitals': vitals_data,
                        'prediction': ("Might have Diabetes" 
                                       if prediction[0] == 1
                                       else "No Diabetes"),
                        'diagnosis': diagnosis[0],
                        'data_quality_report' : pancreas_dq_score.data_quality_value,
                        'missing_columns' : pancreas_dq_score.missing_features
                        },
                        )

            except Exception:
                logger.exception("Error during diabetes prediction")
                return render(request, 'prediction/pancreas/predict.html', 
                              {'form': form, 'error': 'An error occurred while processing your request. '
                               'Please try again.'})

    else:
        form = DiabetesPredictionForm()
        
    return render(request, 'prediction/pancreas/predict.html', {'form': form})

def result(request):
    return render(request, 'pancreas/result.html')
