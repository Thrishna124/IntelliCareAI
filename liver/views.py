########## Import Statements ##########

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render

from liver.forms import LiverPredictionForm

from main_page.models import PredictionData
from main_page.utils.clinical_workspace import get_active_patient
from main_page.utils.prediction_utils import save_dq_score
from main_page.utils.prediction_utils import build_prediction_result
from main_page.utils.model_info import MODEL_INFO
from main_page.utils.prediction_metadata import generate_prediction_metadata


logger = logging.getLogger(__name__)


############ Model Paths ############

MODEL_DIR = Path(__file__).resolve().parent / "models"


@lru_cache(maxsize=1)
def get_prediction_model():
    return joblib.load(MODEL_DIR / "liver_prediction_model.pkl")


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(MODEL_DIR / "liver_preprocessor.pkl")


############ Feature Order ############

NUMERIC_FEATURES = [
    "age",
    "total_bilirubin",
    "direct_bilirubin",
    "alkaline_phosphotase_ALP",
    "alamine_aminotransferase_ALT",
    "aspartate_aminotransferase_AST",
    "total_proteins",
    "albumin",
    "albumin_globulin_ratio",
]

CATEGORICAL_FEATURES = [
    "sex",
]


############ Clinical Interpretation ############

def get_liver_diagnosis(data):
    """
    Generate a rule-based clinical interpretation using
    standard laboratory reference values.
    """

    if (
        data["total_bilirubin"] > 1.2
        or data["direct_bilirubin"] > 0.3
    ):
        return "Possible Liver Disease"

    if data["alkaline_phosphotase_ALP"] > 120:
        return "Possible Bile Duct Obstruction or Liver Disease"

    if (
        data["alamine_aminotransferase_ALT"] > 40
        or data["aspartate_aminotransferase_AST"] > 40
    ):
        return "Possible Hepatitis or Liver Damage"

    if data["albumin"] < 3.5:
        return "Possible Chronic Liver Disease"

    if data["albumin_globulin_ratio"] < 1.0:
        return "Possible Liver Disease"

    return "Normal"


############ Data Processing ############

def process_liver_data(data):
    """
    Prepare input data for the trained liver prediction model.
    """

    df = pd.DataFrame([data])

    expected_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES

    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[expected_columns]
    df = df.fillna(0)

    logger.debug("Liver prediction input:\n%s", df)

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)

########## Recommendation list #################

LIVER_RECOMMENDATIONS = {

    "Very Low": [
        "Maintain a healthy lifestyle.",
        "Continue regular health check-ups.",
        "Avoid excessive alcohol consumption."
    ],

    "Low": [
        "Monitor liver health periodically.",
        "Maintain a balanced diet.",
        "Exercise regularly."
    ],

    "Borderline": [
        "Consult a physician for evaluation.",
        "Schedule Liver Function Tests (LFT).",
        "Reduce alcohol intake.",
        "Maintain a healthy weight."
    ],

    "Moderate": [
        "Consult a hepatologist.",
        "Complete Liver Function Tests.",
        "Consider abdominal ultrasound if advised.",
        "Avoid alcohol completely.",
        "Review current medications with your physician."
    ],

    "High": [
        "Seek immediate medical evaluation.",
        "Consult a hepatologist promptly.",
        "Complete all recommended investigations.",
        "Avoid alcohol and hepatotoxic medications.",
        "Follow up as advised by your healthcare provider."
    ]
}

########### Prediction View ############

@login_required
def predict_liver_disease(request):

    patient_data = get_active_patient(request)

    if patient_data is None:
        return render(
            request,
            "prediction/liver/predict.html",
            {
                "form": LiverPredictionForm(),
                "error": "Select a patient from the Clinical Workspace before starting a prediction.",
            },
        )

    if request.method == "POST":

        form = LiverPredictionForm(request.POST)

        print("=== POST RECEIVED ===")

        if form.is_valid():

            print("=== FORM VALID ===")

            data = form.cleaned_data

            data_for_prediction = {
                "age": patient_data.age,
                "sex": patient_data.sex,
                "total_bilirubin": data["total_bilirubin"],
                "direct_bilirubin": data["direct_bilirubin"],
                "alkaline_phosphotase_ALP": data["alkaline_phosphotase_ALP"],
                "alamine_aminotransferase_ALT": data["alamine_aminotransferase_ALT"],
                "aspartate_aminotransferase_AST": data["aspartate_aminotransferase_AST"],
                "total_proteins": data["total_proteins"],
                "albumin": data["albumin"],
                "albumin_globulin_ratio": data["albumin_globulin_ratio"],
            }

            try:
                
                print("=== ENTERED TRY BLOCK ===")

                input_data = process_liver_data(data_for_prediction)

                prediction_model = get_prediction_model()

                prediction = prediction_model.predict(input_data)

                probability = prediction_model.predict_proba(input_data)[0][1]


                diagnosis = get_liver_diagnosis(data_for_prediction)

                prediction_record = PredictionData(
                    total_bilirubin=data["total_bilirubin"],
                    direct_bilirubin=data["direct_bilirubin"],
                    alkaline_phosphotase_ALP=data["alkaline_phosphotase_ALP"],
                    alamine_aminotransferase_ALT=data["alamine_aminotransferase_ALT"],
                    aspartate_aminotransferase_AST=data["aspartate_aminotransferase_AST"],
                    total_proteins=data["total_proteins"],
                    albumin=data["albumin"],
                    albumin_globulin_ratio=data["albumin_globulin_ratio"],
                    prediction="Yes" if prediction[0] == 1 else "No",
                    prediction_type="liver",
                    diagnosis=diagnosis,
                    pid=patient_data,
                )

                with transaction.atomic():

                    prediction_record.save()

                    data_quality = save_dq_score(
                        prediction_type="liver",
                        patient=patient_data,
                        prediction_data=data_for_prediction,
                    )

                print("=== ABOUT TO RENDER RESULT ===")

                prediction_result = build_prediction_result(
                                probability,
                                "Liver Disease",
                                LIVER_RECOMMENDATIONS,
)

                prediction_metadata = generate_prediction_metadata(
                    model_info=MODEL_INFO["liver"],
                    disease_code="LIV",
                    )

                print( prediction_metadata)
                
                return render(
                    request,
                    "prediction/liver/result.html",
                    {
                        "patient": patient_data,
                        "prediction_result": prediction_result,
                        "prediction_metadata": prediction_metadata,
                        "diagnosis": diagnosis,
                        "data_quality": data_quality,
                    },
                )

            except Exception as e:
                import traceback
                print("=== EXCEPTION ===")

                logger.exception("Error during liver prediction: %s", e)

                traceback.print_exc()

                return render(
                    request,
                    "prediction/liver/predict.html",
                    {
                        "form": form,
                        "error": "An error occurred during prediction. Please try again.",
                    },
                )

        else:
            print("=== FORM INVALID ===")
            print(form.errors)

    else:
        form = LiverPredictionForm()
        print("=== RENDERING PREDICTION FORM ===")

        return render(
            request,
            "prediction/liver/predict.html",
            {
            "form": form,
            },
    )


def result(request):
    print("=== RENDERING RESULT PAGE ===")
    return render(request, "prediction/liver/result.html")