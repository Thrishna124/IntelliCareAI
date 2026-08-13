import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from heart.clinical_interpretation import HEART_INTERPRETATION
from heart.forms import HeartPredictionForm

from main_page.utils.clinical_workspace import get_active_patient
from main_page.utils.model_info import MODEL_INFO
from main_page.services.prediction_service import execute_standard_prediction


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
        MODEL_DIR / "heart_prediction_model.pkl"
    )


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(
        MODEL_DIR / "heart_diagnosis_model.pkl"
    )


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(
        MODEL_DIR / "heart_preprocessor.pkl"
    )


# ============================================================
# Feature Definitions
# ============================================================

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


# ============================================================
# Data Processing
# ============================================================

def process_heart_data(data):
    """
    Prepare heart prediction input for the trained preprocessor.
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
        "Heart prediction input:\n%s",
        df,
    )

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


# ============================================================
# Recommendations
# ============================================================

HEART_RECOMMENDATIONS = {

    "Low Risk": {
        "status": (
            "Heart health appears to be within a healthy range."
        ),
        "recommendations": [
            "Maintain a heart-healthy balanced diet.",
            "Engage in at least 150 minutes of moderate exercise each week.",
            "Maintain a healthy body weight.",
            "Continue routine annual health check-ups.",
            "Avoid smoking and excessive alcohol consumption.",
            "Monitor blood pressure, cholesterol, and blood sugar periodically.",
        ],
    },

    "Moderate Risk": {
        "status": (
            "Several cardiovascular risk factors have been identified."
        ),
        "recommendations": [
            "Consult your primary care physician for further cardiovascular assessment.",
            "Monitor blood pressure and cholesterol regularly.",
            "Reduce dietary salt, saturated fat, and processed foods.",
            "Increase physical activity according to medical advice.",
            "Manage diabetes, hypertension, or other chronic conditions carefully.",
            "Reduce stress through adequate sleep, relaxation techniques, or mindfulness.",
        ],
    },

    "High Risk": {
        "status": (
            "The AI model indicates a high likelihood of cardiovascular disease."
        ),
        "recommendations": [
            "Seek prompt evaluation from a cardiologist or qualified healthcare professional.",
            "Undergo comprehensive cardiac investigations such as ECG, Echocardiogram, or Stress Test if recommended.",
            "Strictly follow prescribed medications and treatment plans.",
            "Immediately address modifiable risk factors including smoking, obesity, uncontrolled diabetes, and hypertension.",
            "Adopt a heart-healthy lifestyle with dietary modifications and physician-approved exercise.",
            "Seek immediate medical attention if experiencing chest pain, shortness of breath, dizziness, or other emergency symptoms.",
        ],
    },
}


# ============================================================
# Prediction View
# ============================================================

@login_required
def predict_heart_disease(request):

    patient_data = get_active_patient(request)

    # --------------------------------------------------------
    # No active patient
    # --------------------------------------------------------

    if patient_data is None:

        return render(
            request,
            "prediction/heart/predict.html",
            {
                "form": HeartPredictionForm(),
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

        form = HeartPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # ------------------------------------------------
            # Build prediction input
            # ------------------------------------------------

            data_for_prediction = {
                "age": patient_data.age,
                "sex": (
                    "0"
                    if patient_data.sex == "Female"
                    else "1"
                ),
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

                # ------------------------------------------------
                # Preprocess
                # ------------------------------------------------

                input_data = process_heart_data(
                    data_for_prediction
                )

                # ------------------------------------------------
                # Load models
                # ------------------------------------------------

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                # ------------------------------------------------
                # Heart disease prediction
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
                    "Heart diagnosis=%s confidence=%s%%",
                    diagnosis,
                    diagnosis_confidence,
                )

                # ------------------------------------------------
                # Clinical interpretation
                # ------------------------------------------------

                clinical_interpretation = (
                    HEART_INTERPRETATION
                    .get(diagnosis, {})
                    .get("description", "")
                )

                # ------------------------------------------------
                # Centralized prediction service
                # ------------------------------------------------

                prediction_workflow = (
                    execute_standard_prediction(
                        patient=patient_data,

                        prediction_type="heart",

                        probability=risk_probability,

                        disease_name="Heart Disease",

                        recommendation_map=(
                            HEART_RECOMMENDATIONS
                        ),

                        prediction_data=(
                            data_for_prediction
                        ),

                        prediction=(
                            "Yes"
                            if prediction[0] == 1
                            else "No"
                        ),

                        model_info=MODEL_INFO["heart"],

                        disease_code="HEA",

                        prediction_fields={
                            "chestpain": data["chestpain"],
                            "restingBP": data["restingBP"],
                            "cholesterol": data["cholesterol"],
                            "fastingbloodsugar": (
                                data["fastingbloodsugar"]
                            ),
                            "restingrelectro": (
                                data["restingrelectro"]
                            ),
                            "maxheartrate": (
                                data["maxheartrate"]
                            ),
                            "exerciseangia": (
                                data["exerciseangia"]
                            ),
                            "oldpeak": data["oldpeak"],
                            "slope": data["slope"],
                            "noofmajorvessels": (
                                data["noofmajorvessels"]
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
                    "prediction/heart/result.html",
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
                    "Error during heart prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/heart/predict.html",
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
            "prediction/heart/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = HeartPredictionForm()

    return render(
        request,
        "prediction/heart/predict.html",
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
        "prediction/heart/result.html",
    )