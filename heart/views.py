########## Import Statements ##########

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from heart.forms import HeartPredictionForm

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
    return joblib.load(MODEL_DIR / "heart_prediction_model.pkl")


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(MODEL_DIR / "heart_diagnosis_model.pkl")


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(MODEL_DIR / "heart_preprocessor.pkl")


NUMERIC_FEATURES = [
    "age",
    "restingBP",
    "cholesterol",
    "fastingbloodsugar",
    "maxheartrate",
    "oldpeak",
]

CATEGORICAL_FEATURES = [
    "sex",
    "chestpain",
    "restingrelectro",
    "exerciseangia",
    "slope",
    "noofmajorvessels",
]

############ Data Processing ############

def process_heart_data(data):
    """
    Prepare heart prediction input for the trained preprocessor.
    """

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

    logger.debug("Heart prediction input:\n%s", df)

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)

############ Prediction View ############

@login_required
def predict_heart_disease(request):

    patient_data = get_active_patient(request)

    if patient_data is None:
        return render(
            request,
            "prediction/heart/predict.html",
            {
                "form": HeartPredictionForm(),
                "error": "Select a patient from the Clinical Workspace before starting a prediction.",
            },
        )

    if request.method == "POST":

        form = HeartPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            data_for_prediction = {
                "age": patient_data.age,
                "sex": "0" if patient_data.sex == "Female" else "1",
                "chestpain": data["chestpain"],
                "restingBP": data["restingBP"],
                "cholesterol": data["cholesterol"],
                "fastingbloodsugar": data["fastingbloodsugar"],
                "restingrelectro": data["restingrelectro"],
                "maxheartrate": data["maxheartrate"],
                "exerciseangia": data["exerciseangia"],
                "oldpeak": data["oldpeak"],
                "slope": data["slope"],
                "noofmajorvessels": data["noofmajorvessels"],
            }

            try:

                input_data = process_heart_data(data_for_prediction)

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                prediction = prediction_model.predict(input_data)
                diagnosis = diagnosis_model.predict(input_data)

                prediction_result = PredictionData(
                    chestpain=data["chestpain"],
                    restingBP=data["restingBP"],
                    cholesterol=data["cholesterol"],
                    fastingbloodsugar=data["fastingbloodsugar"],
                    restingrelectro=data["restingrelectro"],
                    maxheartrate=data["maxheartrate"],
                    exerciseangia=data["exerciseangia"],
                    oldpeak=data["oldpeak"],
                    slope=data["slope"],
                    noofmajorvessels=data["noofmajorvessels"],
                    prediction="Yes" if prediction[0] == 1 else "No",
                    prediction_type="heart",
                    diagnosis=diagnosis[0],
                    pid=patient_data,
                )

                #prediction_result.save()

                #heart_dq_score = save_dq_score(
                #    prediction_type="heart",
                #    patient=patient_data,
                #    prediction_data=data_for_prediction,
                #)

                with transaction.atomic():
                    prediction_result.save()

                    heart_dq_score = save_dq_score(
                    prediction_type="heart",
                    patient=patient_data,
                    prediction_data=data_for_prediction,
                )

                return render(
                    request,
                    "heart/result.html",
                    {
                        "patient": patient_data,
                        "prediction": (
                            "Might have heart problem"
                            if prediction[0] == 1
                            else "Does Not Have heart problem"
                        ),
                        "diagnosis": diagnosis[0],
                        "data_quality_report": heart_dq_score.data_quality_value,
                        "missing_columns": heart_dq_score.missing_features,
                    },
                )

            except Exception:
                logger.exception("Error during heart prediction.")

                return render(
                    request,
                    "prediction/heart/predict.html",
                    {
                        "form": form,
                        "error_message": (
                            "An error occurred during prediction. "
                            "Please try again."
                        ),
                    },
                )

    else:
        form = HeartPredictionForm()

    return render(
        request,
        "prediction/heart/predict.html",
        {
            "form": form,
        },
    )

############ Result View ############

def result(request):
    return render(request, "heart/result.html")
