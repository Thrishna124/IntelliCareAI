import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from liver.forms import LiverPredictionForm

from main_page.services.prediction_service import (
    execute_standard_prediction,
)
from main_page.utils.clinical_workspace import get_active_patient
from main_page.utils.model_info import MODEL_INFO


logger = logging.getLogger(__name__)


# ============================================================
# Model Paths
# ============================================================

MODEL_DIR = Path(__file__).resolve().parent / "models"


# ============================================================
# Model Loading
# ============================================================

@lru_cache(maxsize=1)
def get_prediction_model():
    return joblib.load(
        MODEL_DIR / "liver_prediction_model.pkl"
    )


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(
        MODEL_DIR / "liver_preprocessor.pkl"
    )


# ============================================================
# Feature Order
# ============================================================

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


# ============================================================
# Clinical Interpretation
# ============================================================

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


# ============================================================
# Data Processing
# ============================================================

def process_liver_data(data):
    """
    Prepare input data for the trained liver prediction model.
    """

    df = pd.DataFrame([data])

    expected_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )

    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[expected_columns]
    df = df.fillna(0)

    logger.debug(
        "Liver prediction input:\n%s",
        df,
    )

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


# ============================================================
# Recommendations
# ============================================================

LIVER_RECOMMENDATIONS = {

    "Very Low": {
        "status": (
            "Liver health appears to be within normal limits "
            "with minimal risk indicators."
        ),
        "recommendations": [
            "Maintain a healthy and balanced diet.",
            "Continue regular preventive health check-ups.",
            "Avoid excessive alcohol consumption.",
            "Maintain regular physical activity.",
            "Stay hydrated and maintain a healthy body weight.",
            "Avoid unnecessary use of medications that may affect liver function.",
        ],
    },

    "Low": {
        "status": (
            "Minor liver-related risk factors are present "
            "but no significant abnormalities are indicated."
        ),
        "recommendations": [
            "Monitor liver health during routine medical examinations.",
            "Maintain a balanced diet rich in fruits and vegetables.",
            "Exercise regularly to support overall metabolic health.",
            "Limit alcohol intake.",
            "Maintain a healthy body weight.",
            "Discuss any persistent symptoms with your healthcare provider.",
        ],
    },

    "Borderline": {
        "status": (
            "Borderline liver abnormalities have been identified "
            "and further evaluation is recommended."
        ),
        "recommendations": [
            "Consult a physician for clinical evaluation.",
            "Schedule Liver Function Tests (LFTs).",
            "Reduce or avoid alcohol consumption.",
            "Maintain a healthy weight through diet and exercise.",
            "Review current medications with your healthcare provider.",
            "Repeat laboratory investigations if recommended.",
        ],
    },

    "Moderate": {
        "status": (
            "Several liver-related abnormalities suggest a "
            "moderate likelihood of liver disease."
        ),
        "recommendations": [
            "Consult a hepatologist or gastroenterologist.",
            "Complete comprehensive Liver Function Tests.",
            "Consider abdominal ultrasound or additional imaging if advised.",
            "Avoid alcohol completely.",
            "Review prescription and over-the-counter medications with your physician.",
            "Follow up promptly for further clinical assessment.",
        ],
    },

    "High": {
        "status": (
            "The AI model indicates a high likelihood of liver "
            "disease requiring prompt medical evaluation."
        ),
        "recommendations": [
            "Seek immediate medical evaluation.",
            "Consult a hepatologist as soon as possible.",
            "Complete all recommended laboratory and imaging investigations.",
            "Avoid alcohol and medications that may cause liver injury unless prescribed.",
            "Follow all treatment recommendations provided by your healthcare professional.",
            "Seek urgent medical attention if you develop jaundice, severe abdominal pain, confusion, vomiting blood, or significant swelling.",
        ],
    },
}


# ============================================================
# Prediction View
# ============================================================

@login_required
def predict_liver_disease(request):

    patient_data = get_active_patient(request)

    # --------------------------------------------------------
    # No active patient
    # --------------------------------------------------------

    if patient_data is None:

        return render(
            request,
            "prediction/liver/predict.html",
            {
                "form": LiverPredictionForm(),
                "error": (
                    "Select a patient from the Clinical Workspace "
                    "before starting a prediction."
                ),
            },
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = LiverPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # ------------------------------------------------
            # Build prediction input
            # ------------------------------------------------

            data_for_prediction = {
                "age": patient_data.age,
                "sex": patient_data.sex,
                "total_bilirubin": (
                    data["total_bilirubin"]
                ),
                "direct_bilirubin": (
                    data["direct_bilirubin"]
                ),
                "alkaline_phosphotase_ALP": (
                    data["alkaline_phosphotase_ALP"]
                ),
                "alamine_aminotransferase_ALT": (
                    data["alamine_aminotransferase_ALT"]
                ),
                "aspartate_aminotransferase_AST": (
                    data["aspartate_aminotransferase_AST"]
                ),
                "total_proteins": (
                    data["total_proteins"]
                ),
                "albumin": data["albumin"],
                "albumin_globulin_ratio": (
                    data["albumin_globulin_ratio"]
                ),
            }

            try:

                # ------------------------------------------------
                # Preprocess
                # ------------------------------------------------

                input_data = process_liver_data(
                    data_for_prediction
                )

                # ------------------------------------------------
                # Load model
                # ------------------------------------------------

                prediction_model = get_prediction_model()

                # ------------------------------------------------
                # Liver prediction
                # ------------------------------------------------

                prediction = prediction_model.predict(
                    input_data
                )

                probability = (
                    prediction_model
                    .predict_proba(input_data)[0][1]
                )

                # ------------------------------------------------
                # Rule-based clinical diagnosis
                # ------------------------------------------------

                diagnosis = get_liver_diagnosis(
                    data_for_prediction
                )

                logger.info(
                    "Liver diagnosis=%s",
                    diagnosis,
                )

                # ------------------------------------------------
                # Centralized prediction service
                # ------------------------------------------------

                prediction_workflow = (
                    execute_standard_prediction(
                        patient=patient_data,

                        prediction_type="liver",

                        probability=probability,

                        disease_name="Liver Disease",

                        recommendation_map=(
                            LIVER_RECOMMENDATIONS
                        ),

                        prediction_data=(
                            data_for_prediction
                        ),

                        prediction=(
                            "Yes"
                            if prediction[0] == 1
                            else "No"
                        ),

                        model_info=MODEL_INFO["liver"],

                        disease_code="LIV",

                        prediction_fields={
                            "total_bilirubin": (
                                data["total_bilirubin"]
                            ),
                            "direct_bilirubin": (
                                data["direct_bilirubin"]
                            ),
                            "alkaline_phosphotase_ALP": (
                                data[
                                    "alkaline_phosphotase_ALP"
                                ]
                            ),
                            "alamine_aminotransferase_ALT": (
                                data[
                                    "alamine_aminotransferase_ALT"
                                ]
                            ),
                            "aspartate_aminotransferase_AST": (
                                data[
                                    "aspartate_aminotransferase_AST"
                                ]
                            ),
                            "total_proteins": (
                                data["total_proteins"]
                            ),
                            "albumin": (
                                data["albumin"]
                            ),
                            "albumin_globulin_ratio": (
                                data[
                                    "albumin_globulin_ratio"
                                ]
                            ),
                        },

                        diagnosis=diagnosis,
                    )
                )

                # ------------------------------------------------
                # Render result
                # ------------------------------------------------

                return render(
                    request,
                    "prediction/liver/result.html",
                    {
                        "patient": patient_data,

                        "prediction_result": (
                            prediction_workflow[
                                "prediction_result"
                            ]
                        ),

                        "prediction_metadata": (
                            prediction_workflow[
                                "prediction_metadata"
                            ]
                        ),

                        "diagnosis": diagnosis,

                        "diagnosis_confidence": round(
                            probability * 100,
                                1,
                        ),

                        "data_quality": (
                            prediction_workflow[
                                "data_quality"
                            ]
                        ),
                    },
                )

            except Exception as e:

                logger.exception(
                    "Error during liver prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/liver/predict.html",
                    {
                        "form": form,
                        "error": (
                            "An error occurred during "
                            "prediction. Please try again."
                        ),
                    },
                )

        # --------------------------------------------------------
        # Invalid form
        # --------------------------------------------------------

        return render(
            request,
            "prediction/liver/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = LiverPredictionForm()

    return render(
        request,
        "prediction/liver/predict.html",
        {
            "form": form,
        },
    )


# ============================================================
# Result View
# ============================================================

@login_required
def result(request):

    return render(
        request,
        "prediction/liver/result.html",
    )