########## Import Statements ##########

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from kidney.forms import KidneyPredictionForm

from main_page.models import (
    PatientData,
    PredictionData,
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
    return joblib.load(MODEL_DIR / "kidney_prediction_model.pkl")


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(MODEL_DIR / "kidney_diagnosis_model.pkl")


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(MODEL_DIR / "kidney_preprocessor.pkl")

NUMERIC_FEATURES = [
    "bp","bgr","bu","sc","sod","pot",
    "hemo","pcv","wc","rc"  
]

CATEGORICAL_FEATURES = [
    "al","su","rbc","pc",
    "pcc","ba","htn","dm",
    "cad","appet","pe","ane"
]

############ Data Processing ############

def process_kidney_data(data):
    """
    Prepare kidney prediction input for the trained preprocessor.
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

    logger.debug("Kidney prediction input:\n%s", df)

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


############ Prediction View ############

@login_required
def predict_kidney_disease(request):

    patient_data = get_active_patient(request)

    if patient_data is None:
        return render(
            request,
            "prediction/kidney/predict.html",
            {
                "form": KidneyPredictionForm(),
                "error": "Select a patient from the Clinical Workspace before starting a prediction.",
            },
        )

    if request.method == "POST":

        form = KidneyPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            data_for_prediction = {
                'age': patient_data.age,
                'bp': data['bp'],
                'sg': data['sg'],
                'al': data['al'],
                'su':data['su'],
                'bu': data['bu'],
                'rbc': data['rbc'],
                'pc': data['pc'],
                'pcc': data['pcc'],
                'ba': data['ba'],
                'bgr': data['bgr'],
                'sc': data['sc'],
                'sod': data['sod'],
                'pot': data['pot'],
                'hemo': data['hemo'],
                'pcv': data['pcv'],
                'wc': data['wc'],
                'rc': data['rc'],
                'htn': data['htn'],
                'dm': data['dm'],
                'cad': data['cad'],
                'appet': data['appet'],
                'pe': data['pe'],
                'ane': data['ane'],
            }
        try:
                input_data = process_kidney_data(data_for_prediction)

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                prediction = prediction_model.predict(input_data)
                diagnosis = diagnosis_model.predict(input_data)
                
                # Save data to the UnifiedPrediction table
                prediction_result = PredictionData(
                    pid=patient_data,
                    bp=data['bp'],
                    sg=data['sg'],
                    al=data['al'],
                    su=data['su'],
                    bu=data['bu'],
                    rbc=data['rbc'],
                    pc=data['pc'],
                    pcc=data['pcc'],
                    ba=data['ba'],
                    bgr=data['bgr'],
                    sc=data['sc'],
                    sod=data['sod'],
                    pot=data['pot'],
                    hemo=data['hemo'],
                    pcv=data['pcv'],
                    wc=data['wc'],
                    rc=data['rc'],
                    htn=data['htn'],
                    dm=data['dm'],
                    cad=data['cad'],
                    appet=data['appet'],
                    pe=data['pe'],
                    ane=data['ane'],
                    prediction="Yes" if prediction[0] == 1 else "No",
                    prediction_type='kidney' , # Set prediction type to 'kidney'
                    diagnosis = diagnosis[0]
                )

                with transaction.atomic():
                    prediction_result.save()

                    kidney_dq_score = save_dq_score(
                    prediction_type="kidney",
                    patient=patient_data,
                    prediction_data=data_for_prediction,
                )
                try:
                    prediction_result.save()
                    kidney_dq_score.save()
                except Exception as e:
                    logger.error("Unable to save prediction.")
                return render(request, 'kidney/result.html', 
             {
                    'patient': patient_data,
                    #'vitals': vitals_data,
                    'prediction': ("Might have kidney problem" 
                    if prediction[0] == 1 
                    else 
                    "Do not have any kidney problem"),
                    'diagnosis': diagnosis[0],
                    'data_quality_report' : kidney_dq_score.data_quality_value,
                    'missing_columns' : kidney_dq_score.missing_features
                })

        except Exception as e:
                logger.error("Error during kidneys prediction")
                return render(request, 'prediction/kidneys/predict.html', 
                              {'form': form, 'error':  "An error occurred during prediction. "
                            "Please try again."})
    else:
        form = KidneyPredictionForm()

    return render(request, 'prediction/kidneys/predict.html', {'form': form})



def result(request):
    # You can add logic here for the result view
    return render(request, 'kidney/result.html')

