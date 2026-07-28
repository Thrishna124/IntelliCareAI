########## Import Statements ##########

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from lungs.forms import LungsPredictionForm

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
    return joblib.load(MODEL_DIR / "lung_prediction_model.pkl")


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(MODEL_DIR / "lung_diagnosis_model.pkl")


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(MODEL_DIR / "lung_preprocessor.pkl")


NUMERIC_FEATURES = [
    "age",
    "height",
    "weight",
    "predicted_FEV1",
    "predicted_VC",
    "actual_FEV1",
    "actual_VC",
    "fev1_vc_ratio",
]

CATEGORICAL_FEATURES = [
    "sex"
]

############ Data Processing Function ##########

def process_lungs_data(data):
    """
    Prepare lung prediction input for the trained preprocessor.
    """
    # Convert the input data (which is likely a dictionary) to a DataFrame
    
    df = pd.DataFrame(data)

    expected_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES

    # Ensure every expected feature exists
    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.NA

    # Arrange columns in training order
    df = df[expected_columns]

    # Replace missing values
    df = df.fillna(0)

    logger.debug("Lung prediction input:\n%s", df)

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)



##################### Prediction Views ####################

@login_required
def predict_lung_disease(request):
    # Fetch the patient data from PatientData and FormVitals tables
    patient_data = get_active_patient(request)
    if patient_data is None:
        return render(
            request,
            "prediction/lungs/predict.html",
            {
                "form": LungsPredictionForm(),
                "error": "Select a patient from the Clinical Workspace before starting a prediction.",
            },
        )

    vitals_data = FormVitals.objects.filter(pid=patient_data).order_by('-id').first()
    logger.debug(f"Vitals Data: {vitals_data}")  # Ensure vitals_data is correctly populated

    if request.method == 'POST':
        form = LungsPredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Prepare data for prediction
            data_for_prediction = {
                'age': patient_data.age,
                'sex': patient_data.sex,
                'height':vitals_data.height,
                'weight':vitals_data.weight,
                'predicted_FEV1': data['predicted_FEV1'],
                'predicted_VC': data['predicted_VC'],
                'actual_FEV1': data['actual_FEV1'],
                'actual_VC': data['actual_VC'],
                'fev1_vc_ratio': data['fev1_vc_ratio'],
            }
            
            try:
                input_data = process_lungs_data(data_for_prediction)

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                prediction = prediction_model.predict(input_data)
                diagnosis = diagnosis_model.predict(input_data)
                
                # Save data to the PredictionData table
                prediction_result = PredictionData(
                    predicted_FEV1=data['predicted_FEV1'],
                    predicted_VC=data['predicted_VC'],
                    actual_FEV1=data['actual_FEV1'],
                    actual_VC=data['actual_VC'],
                    fev1_vc_ratio=data['fev1_vc_ratio'],
                    prediction="Yes" if prediction[0] == 1 else "No",
                    prediction_type='lungs',
                    diagnosis=diagnosis[0],
                    pid=patient_data
                )

                with transaction.atomic():
                    prediction_result.save()

                    lungs_dq_score = save_dq_score(
                    prediction_type="lungs",
                    patient=patient_data,
                    prediction_data=data_for_prediction,
                )

                #try:
                #    prediction_result.save()
                #    lungs_dq_score.save()
                #except Exception:
                #    logger.exception("Unable to save prediction.")
                #    raise


                # Render the result page with the prediction and diagnosis
                return render(request, 'lungs/result.html', {
                    'patient': patient_data,
                    #'vitals': vitals_data,
                    'prediction': ("Might have Lung disorder" 
                    if prediction[0] == 1 
                    else 
                    "Do not have any Lung disorder"),
                    'diagnosis': diagnosis[0],
                    'data_quality_report' : lungs_dq_score.data_quality_value,
                    'missing_columns' : lungs_dq_score.missing_features
                })

            except Exception as e:
                logger.error("Error during lungs prediction")
                return render(request, 'prediction/lungs/predict.html', 
                              {'form': form, 'error':  "An error occurred during prediction. "
                            "Please try again."})

    else:
        form = LungsPredictionForm()
        
    return render(request, 'prediction/lungs/predict.html', {'form': form})

def result(request):
    return render(request, 'lungs/result.html')
