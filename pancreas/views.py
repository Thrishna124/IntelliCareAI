import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from pancreas.forms import DiabetesPredictionForm

from main_page.models import FormVitals
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
        MODEL_DIR / "diabetes_prediction_model.pkl"
    )


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(
        MODEL_DIR / "diabetes_diagnosis_model.pkl"
    )


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(
        MODEL_DIR / "diabetes_preprocessor.pkl"
    )


# ============================================================
# Feature Definitions
# ============================================================

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
    "sex",
]


# ============================================================
# Data Processing
# ============================================================

def process_diabetes_data(data):
    """
    Prepare diabetes prediction input for the trained preprocessor.
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
        "Diabetes prediction input:\n%s",
        df,
    )

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


# ============================================================
# Recommendations
# ============================================================

DIABETES_RECOMMENDATIONS = {

    "Very Low": {
        "status": (
            "Blood glucose levels appear to be within a healthy "
            "range with minimal indicators of diabetes risk."
        ),
        "recommendations": [
            "Maintain a balanced and nutritious diet.",
            "Continue regular physical activity.",
            "Maintain a healthy body weight.",
            "Schedule routine annual health check-ups.",
            "Monitor blood glucose periodically as recommended.",
            "Avoid excessive intake of sugary foods and beverages.",
        ],
    },

    "Low": {
        "status": (
            "A small number of diabetes risk factors have been "
            "identified, but the overall likelihood remains low."
        ),
        "recommendations": [
            "Continue a healthy lifestyle.",
            "Exercise for at least 150 minutes each week.",
            "Maintain a healthy body weight.",
            "Limit refined carbohydrates and sugary drinks.",
            "Monitor blood glucose during routine medical visits.",
            "Discuss any family history of diabetes with your healthcare provider.",
        ],
    },

    "Borderline": {
        "status": (
            "Borderline diabetes risk has been detected. Early "
            "lifestyle changes may help reduce progression."
        ),
        "recommendations": [
            "Consult your primary care physician for evaluation.",
            "Schedule fasting blood glucose or HbA1c testing.",
            "Adopt a balanced diet with controlled carbohydrate intake.",
            "Increase physical activity.",
            "Aim for gradual weight reduction if overweight.",
            "Monitor blood glucose regularly.",
        ],
    },

    "Moderate": {
        "status": (
            "Several diabetes risk factors have been identified "
            "that require clinical attention."
        ),
        "recommendations": [
            "Consult an endocrinologist or primary care physician.",
            "Complete HbA1c and fasting blood glucose investigations.",
            "Follow a structured diabetic meal plan.",
            "Exercise regularly under medical guidance.",
            "Monitor blood glucose as advised by your healthcare provider.",
            "Manage blood pressure and cholesterol alongside blood sugar.",
        ],
    },

    "High": {
        "status": (
            "The AI model indicates a high likelihood of diabetes "
            "requiring prompt medical evaluation."
        ),
        "recommendations": [
            "Seek prompt medical evaluation.",
            "Consult an endocrinologist as soon as possible.",
            "Complete HbA1c, fasting glucose, and additional recommended investigations.",
            "Begin lifestyle modifications immediately under medical supervision.",
            "Follow prescribed medications and monitoring schedules.",
            "Seek immediate medical attention if experiencing excessive thirst, frequent urination, unexplained weight loss, blurred vision, or symptoms of diabetic emergencies.",
        ],
    },
}


# ============================================================
# Prediction View
# ============================================================

@login_required
def predict_diabetes(request):

    # --------------------------------------------------------
    # Active patient
    # --------------------------------------------------------

    patient_data = get_active_patient(request)

    if patient_data is None:

        return render(
            request,
            "prediction/pancreas/predict.html",
            {
                "form": DiabetesPredictionForm(),
                "error": (
                    "Select a patient from the Clinical Workspace "
                    "before starting a prediction."
                ),
            },
        )

    # --------------------------------------------------------
    # Latest patient vitals
    # --------------------------------------------------------

    vitals_data = (
        FormVitals.objects
        .filter(pid=patient_data)
        .order_by("-id")
        .first()
    )

    if vitals_data is None:

        return render(
            request,
            "prediction/pancreas/predict.html",
            {
                "form": DiabetesPredictionForm(),
                "error": (
                    "Patient vitals are required before prediction."
                ),
            },
        )

    logger.debug(
        "Diabetes prediction vitals: %s",
        vitals_data,
    )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = DiabetesPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # ------------------------------------------------
            # Build prediction input
            # ------------------------------------------------

            data_for_prediction = {
                "age": patient_data.age,

                "sex": (
                    "M"
                    if patient_data.sex == "Male"
                    else "F"
                ),

                "BMI": vitals_data.BMI,

                "urea": data["urea"],
                "creatinine": data["creatinine"],
                "hba1c": data["hba1c"],
                "cholesterol": data["cholesterol"],
                "triglycerides": data["triglycerides"],
                "HDL": data["HDL"],
                "LDL": data["LDL"],
                "VLDL": data["VLDL"],
            }

            try:

                # ------------------------------------------------
                # Preprocess
                # ------------------------------------------------

                input_data = process_diabetes_data(
                    data_for_prediction
                )

                # ------------------------------------------------
                # Load models
                # ------------------------------------------------

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                # ------------------------------------------------
                # Diabetes prediction
                # ------------------------------------------------

                probability = (
                    prediction_model
                    .predict_proba(input_data)[0][1]
                )

                prediction = prediction_model.predict(
                    input_data
                )

                # ------------------------------------------------
                # Diagnosis prediction
                # ------------------------------------------------

                diagnosis_probs = (
                    diagnosis_model
                    .predict_proba(input_data)[0]
                )

                best_idx = diagnosis_probs.argmax()

                diagnosis = (
                    diagnosis_model.classes_[best_idx]
                )

                diagnosis_confidence = round(
                    diagnosis_probs[best_idx] * 100,
                    1,
                )

                logger.info(
                    "Diabetes diagnosis=%s confidence=%s%%",
                    diagnosis,
                    diagnosis_confidence,
                )

                # ------------------------------------------------
                # Centralized prediction service
                # ------------------------------------------------

                prediction_workflow = (
                    execute_standard_prediction(
                        patient=patient_data,

                        prediction_type="pancreas",

                        probability=probability,

                        disease_name="Pancreas Disease",

                        recommendation_map=(
                            DIABETES_RECOMMENDATIONS
                        ),

                        prediction_data=(
                            data_for_prediction
                        ),

                        prediction=(
                            "Yes"
                            if prediction[0] == 1
                            else "No"
                        ),

                        model_info=MODEL_INFO["pancreas"],

                        disease_code="PAN",

                        prediction_fields={
                            "urea": data["urea"],
                            "creatinine": data["creatinine"],
                            "hba1c": data["hba1c"],
                            "cholesterol": data["cholesterol"],
                            "triglycerides": (
                                data["triglycerides"]
                            ),
                            "HDL": data["HDL"],
                            "LDL": data["LDL"],
                            "VLDL": data["VLDL"],
                        },

                        diagnosis=diagnosis,
                    )
                )

                # ------------------------------------------------
                # Render result
                # ------------------------------------------------

                return render(
                    request,
                    "prediction/pancreas/result.html",
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

                        "data_quality": (
                            prediction_workflow[
                                "data_quality"
                            ]
                        ),
                    },
                )

            except Exception as e:

                logger.exception(
                    "Error during diabetes prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/pancreas/predict.html",
                    {
                        "form": form,
                        "error": (
                            "An error occurred while processing "
                            "your request. Please try again."
                        ),
                    },
                )

        # --------------------------------------------------------
        # Invalid form
        # --------------------------------------------------------

        return render(
            request,
            "prediction/pancreas/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = DiabetesPredictionForm()

    return render(
        request,
        "prediction/pancreas/predict.html",
        {
            "form": form,
        },
    )


# ============================================================
# Result View
# ============================================================

def result(request):

    return render(
        request,
        "prediction/pancreas/result.html",
    )