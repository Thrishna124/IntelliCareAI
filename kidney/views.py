import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from kidney.clinical_interpretation import KIDNEY_INTERPRETATION
from kidney.forms import KidneyPredictionForm

from main_page.utils.clinical_workspace import get_active_patient
from main_page.utils.model_info import MODEL_INFO
from main_page.services.prediction_service import (
    execute_standard_prediction,
)


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
        MODEL_DIR / "kidney_prediction_model.pkl"
    )


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(
        MODEL_DIR / "kidney_diagnosis_model.pkl"
    )


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(
        MODEL_DIR / "kidney_preprocessor.pkl"
    )


# ============================================================
# Feature Definitions
# ============================================================

NUMERIC_FEATURES = [
    "age",
    "bp",
    "sg",
    "bgr",
    "bu",
    "sc",
    "sod",
    "pot",
    "hemo",
    "pcv",
    "wc",
    "rc",
]


CATEGORICAL_FEATURES = [
    "al",
    "su",
    "rbc",
    "pc",
    "pcc",
    "ba",
    "htn",
    "dm",
    "cad",
    "appet",
    "pe",
    "ane",
]


# ============================================================
# Data Processing
# ============================================================

def process_kidney_data(data):
    """
    Prepare kidney prediction input for the trained preprocessor.
    """

    df = pd.DataFrame([data])

    expected_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )

    # Ensure every expected feature exists
    for column in expected_columns:
        if column not in df.columns:
            df[column] = pd.NA

    # Arrange columns in training order
    df = df[expected_columns]

    # Replace missing values
    df = df.fillna(0)

    logger.debug(
        "Kidney prediction input:\n%s",
        df,
    )

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


# ============================================================
# Recommendations
# ============================================================

KIDNEY_RECOMMENDATIONS = {

    "Low Risk": {
        "status": (
            "The kidney health indicators do not currently "
            "suggest a significant risk."
        ),
        "recommendations": [
            "Maintain adequate hydration unless otherwise advised by your healthcare provider.",
            "Maintain a balanced diet with appropriate salt and protein intake.",
            "Maintain a healthy body weight and stay physically active.",
            "Monitor blood pressure and blood sugar regularly.",
            "Continue routine health check-ups and kidney function monitoring.",
        ],
    },

    "Moderate Risk": {
        "status": (
            "Some clinical indicators suggest that kidney "
            "health should be monitored more closely."
        ),
        "recommendations": [
            "Consult your healthcare professional for further kidney health assessment.",
            "Monitor blood pressure and blood sugar regularly.",
            "Maintain adequate hydration unless medically restricted.",
            "Reduce excessive salt and processed food consumption.",
            "Follow medical advice regarding diabetes, hypertension, or other chronic conditions.",
            "Consider follow-up kidney function testing as recommended by your healthcare provider.",
        ],
    },

    "High Risk": {
        "status": (
            "The AI model indicates a high likelihood of "
            "kidney-related abnormality."
        ),
        "recommendations": [
            "Seek prompt evaluation from a qualified healthcare professional.",
            "Discuss kidney function testing and further clinical evaluation with your physician.",
            "Follow prescribed medications and treatment plans carefully.",
            "Monitor blood pressure and blood sugar closely.",
            "Follow dietary and fluid recommendations provided by your healthcare professional.",
            "Seek urgent medical attention if severe symptoms or sudden deterioration occur.",
        ],
    },
}


# ============================================================
# Prediction View
# ============================================================

@login_required
def predict_kidney_disease(request):

    patient_data = get_active_patient(request)

    # --------------------------------------------------------
    # No active patient
    # --------------------------------------------------------

    if patient_data is None:

        return render(
            request,
            "prediction/kidney/predict.html",
            {
                "form": KidneyPredictionForm(),
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

        form = KidneyPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # ------------------------------------------------
            # Build prediction input
            # ------------------------------------------------

            data_for_prediction = {
                "age": patient_data.age,
                "bp": data["bp"],
                "sg": data["sg"],
                "al": data["al"],
                "su": data["su"],
                "bu": data["bu"],
                "rbc": data["rbc"],
                "pc": data["pc"],
                "pcc": data["pcc"],
                "ba": data["ba"],
                "bgr": data["bgr"],
                "sc": data["sc"],
                "sod": data["sod"],
                "pot": data["pot"],
                "hemo": data["hemo"],
                "pcv": data["pcv"],
                "wc": data["wc"],
                "rc": data["rc"],
                "htn": data["htn"],
                "dm": data["dm"],
                "cad": data["cad"],
                "appet": data["appet"],
                "pe": data["pe"],
                "ane": data["ane"],
            }

            try:

                # ------------------------------------------------
                # Preprocess
                # ------------------------------------------------

                input_data = process_kidney_data(
                    data_for_prediction
                )

                # ------------------------------------------------
                # Load models
                # ------------------------------------------------

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                # ------------------------------------------------
                # Kidney prediction
                # ------------------------------------------------

                prediction = prediction_model.predict(
                    input_data
                )

                risk_probability = (
                    prediction_model
                    .predict_proba(input_data)[0][1]
                )

                # ------------------------------------------------
                # Diagnosis prediction
                # ------------------------------------------------

                probs = (
                    diagnosis_model
                    .predict_proba(input_data)[0]
                )

                best_idx = probs.argmax()

                diagnosis = (
                    diagnosis_model.classes_[best_idx]
                )

                diagnosis_confidence = round(
                    probs[best_idx] * 100,
                    1,
                )

                logger.info(
                    "Kidney diagnosis=%s confidence=%s%%",
                    diagnosis,
                    diagnosis_confidence,
                )

                # ------------------------------------------------
                # Clinical interpretation
                # ------------------------------------------------

                clinical_interpretation = (
                    KIDNEY_INTERPRETATION
                    .get(diagnosis, {})
                    .get("description", "")
                )

                # ------------------------------------------------
                # Centralized prediction service
                # ------------------------------------------------

                prediction_workflow = (
                    execute_standard_prediction(
                        patient=patient_data,

                        prediction_type="kidney",

                        probability=risk_probability,

                        disease_name="Kidney Disease",

                        recommendation_map=(
                            KIDNEY_RECOMMENDATIONS
                        ),

                        prediction_data=(
                            data_for_prediction
                        ),

                        prediction=(
                            "Yes"
                            if prediction[0] == 1
                            else "No"
                        ),

                        model_info=MODEL_INFO["kidney"],

                        disease_code="KID",

                        prediction_fields={
                            "bp": data["bp"],
                            "sg": data["sg"],
                            "al": data["al"],
                            "su": data["su"],
                            "bu": data["bu"],
                            "rbc": data["rbc"],
                            "pc": data["pc"],
                            "pcc": data["pcc"],
                            "ba": data["ba"],
                            "bgr": data["bgr"],
                            "sc": data["sc"],
                            "sod": data["sod"],
                            "pot": data["pot"],
                            "hemo": data["hemo"],
                            "pcv": data["pcv"],
                            "wc": data["wc"],
                            "rc": data["rc"],
                            "htn": data["htn"],
                            "dm": data["dm"],
                            "cad": data["cad"],
                            "appet": data["appet"],
                            "pe": data["pe"],
                            "ane": data["ane"],
                        },

                        diagnosis=diagnosis,
                    )
                )

                # ------------------------------------------------
                # Render result
                # ------------------------------------------------

                return render(
                    request,
                    "prediction/kidney/result.html",
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

                        "diagnosis_confidence": (
                            diagnosis_confidence
                        ),

                        "clinical_interpretation": (
                            clinical_interpretation
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
                    "Error during kidney prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/kidney/predict.html",
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
            "prediction/kidney/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = KidneyPredictionForm()

    return render(
        request,
        "prediction/kidney/predict.html",
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
        "prediction/kidney/result.html",
    )