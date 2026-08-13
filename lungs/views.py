import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from lungs.clinical_interpretation import LUNGS_INTERPRETATION
from lungs.forms import LungsPredictionForm

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
        MODEL_DIR / "lung_prediction_model.pkl"
    )


@lru_cache(maxsize=1)
def get_diagnosis_model():
    return joblib.load(
        MODEL_DIR / "lung_diagnosis_model.pkl"
    )


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(
        MODEL_DIR / "lung_preprocessor.pkl"
    )


# ============================================================
# Feature Definitions
# ============================================================

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
    "sex",
]


# ============================================================
# Data Processing
# ============================================================

def process_lungs_data(data):
    """
    Prepare lung prediction input for the trained preprocessor.
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
        "Lung prediction input:\n%s",
        df,
    )

    preprocessor = get_preprocessor()

    return preprocessor.transform(df)


# ============================================================
# Recommendations
# ============================================================

LUNGS_RECOMMENDATIONS = {

    "Low Risk": {
        "status": (
            "The respiratory indicators do not currently "
            "suggest a significant lung disorder risk."
        ),
        "recommendations": [
            "Maintain regular physical activity appropriate for your health condition.",
            "Avoid smoking and exposure to second-hand smoke.",
            "Avoid prolonged exposure to dust, fumes, and other respiratory irritants.",
            "Maintain a healthy body weight.",
            "Continue routine health check-ups and respiratory monitoring when appropriate.",
        ],
    },

    "Moderate Risk": {
        "status": (
            "Some respiratory indicators suggest that further "
            "monitoring may be appropriate."
        ),
        "recommendations": [
            "Consult your healthcare professional for further respiratory assessment.",
            "Discuss pulmonary function testing and follow-up evaluation if recommended.",
            "Avoid smoking and exposure to environmental respiratory irritants.",
            "Maintain appropriate physical activity according to medical advice.",
            "Monitor for persistent cough, breathlessness, wheezing, or reduced exercise tolerance.",
        ],
    },

    "High Risk": {
        "status": (
            "The AI model indicates a high likelihood of "
            "a respiratory abnormality."
        ),
        "recommendations": [
            "Seek prompt evaluation from a qualified healthcare professional.",
            "Discuss comprehensive pulmonary assessment and follow-up testing with your physician.",
            "Avoid smoking and exposure to respiratory irritants.",
            "Follow prescribed medications and treatment plans carefully.",
            "Seek medical attention if breathing difficulties or other significant respiratory symptoms worsen.",
        ],
    },
}


# ============================================================
# Prediction View
# ============================================================

@login_required
def predict_lung_disease(request):

    # --------------------------------------------------------
    # Active patient
    # --------------------------------------------------------

    patient_data = get_active_patient(request)

    if patient_data is None:

        return render(
            request,
            "prediction/lungs/predict.html",
            {
                "form": LungsPredictionForm(),
                "error": (
                    "Select a patient from the Clinical Workspace "
                    "before starting a prediction."
                ),
            },
        )

    # --------------------------------------------------------
    # Latest vitals
    # --------------------------------------------------------

    vitals_data = (
        FormVitals.objects
        .filter(pid=patient_data)
        .order_by("-id")
        .first()
    )

    logger.debug(
        "Lung prediction vitals: %s",
        vitals_data,
    )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = LungsPredictionForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # ------------------------------------------------
            # Ensure vitals exist
            # ------------------------------------------------

            if vitals_data is None:

                return render(
                    request,
                    "prediction/lungs/predict.html",
                    {
                        "form": form,
                        "error": (
                            "Patient height and weight are required "
                            "for lung prediction. Please enter the "
                            "patient's vitals first."
                        ),
                    },
                )

            # ------------------------------------------------
            # Build prediction input
            # ------------------------------------------------

            data_for_prediction = {
                "age": patient_data.age,
                "sex": patient_data.sex,
                "height": vitals_data.height,
                "weight": vitals_data.weight,
                "predicted_FEV1": (
                    data["predicted_FEV1"]
                ),
                "predicted_VC": (
                    data["predicted_VC"]
                ),
                "actual_FEV1": (
                    data["actual_FEV1"]
                ),
                "actual_VC": (
                    data["actual_VC"]
                ),
                "fev1_vc_ratio": (
                    data["fev1_vc_ratio"]
                ),
            }

            try:

                # ------------------------------------------------
                # Preprocess
                # ------------------------------------------------

                input_data = process_lungs_data(
                    data_for_prediction
                )

                # ------------------------------------------------
                # Load models
                # ------------------------------------------------

                prediction_model = get_prediction_model()
                diagnosis_model = get_diagnosis_model()

                # ------------------------------------------------
                # Lung disease prediction
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
                    "Lung diagnosis=%s confidence=%s%%",
                    diagnosis,
                    diagnosis_confidence,
                )

                # ------------------------------------------------
                # Clinical interpretation
                # ------------------------------------------------

                clinical_interpretation = (
                    LUNGS_INTERPRETATION
                    .get(diagnosis, {})
                    .get("description", "")
                )

                # ------------------------------------------------
                # Centralized prediction service
                # ------------------------------------------------

                prediction_workflow = (
                    execute_standard_prediction(
                        patient=patient_data,

                        prediction_type="lungs",

                        probability=risk_probability,

                        disease_name="Lung Disease",

                        recommendation_map=(
                            LUNGS_RECOMMENDATIONS
                        ),

                        prediction_data=(
                            data_for_prediction
                        ),

                        prediction=(
                            "Yes"
                            if prediction[0] == 1
                            else "No"
                        ),

                        model_info=MODEL_INFO["lungs"],

                        disease_code="LUN",

                        prediction_fields={
                            "predicted_FEV1": (
                                data["predicted_FEV1"]
                            ),
                            "predicted_VC": (
                                data["predicted_VC"]
                            ),
                            "actual_FEV1": (
                                data["actual_FEV1"]
                            ),
                            "actual_VC": (
                                data["actual_VC"]
                            ),
                            "fev1_vc_ratio": (
                                data["fev1_vc_ratio"]
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
                    "prediction/lungs/result.html",
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
                    "Error during lung prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/lungs/predict.html",
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
            "prediction/lungs/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = LungsPredictionForm()

    return render(
        request,
        "prediction/lungs/predict.html",
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
        "prediction/lungs/result.html",
    )