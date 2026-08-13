import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from fitness.forms import FitnessForm

from main_page.models import FormVitals
from main_page.services.prediction_service import (
    save_prediction_record,
)
from main_page.utils.clinical_workspace import get_active_patient
from main_page.utils.model_info import MODEL_INFO
from main_page.utils.prediction_metadata import (
    generate_prediction_metadata,
)
from main_page.utils.prediction_utils import (
    build_fitness_result,
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
        MODEL_DIR / "fitness_model.pkl"
    )


@lru_cache(maxsize=1)
def get_preprocessor():
    return joblib.load(
        MODEL_DIR / "fitness_preprocessor.pkl"
    )


# ============================================================
# Feature Definitions
# ============================================================

NUMERIC_FEATURES = [
    "age",
    "height",
    "weight",
    "total_steps",
    "calories_burned",
    "daily_calories_needed",
]


CATEGORICAL_FEATURES = [
    "sex",
    "activity_level",
]


# ============================================================
# Fitness Calculations
# ============================================================

def daily_calories_needed(
    bmr,
    activity_level,
):
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "super_active": 1.9,
    }

    return round(
        bmr
        * activity_multipliers.get(
            activity_level,
            1.2,
        ),
        2,
    )


def calculate_bmr(
    weight,
    height,
    age,
    gender,
):
    if gender == "Male":

        return round(
            (10 * weight)
            + (6.25 * height)
            - (5 * age)
            + 5,
            2,
        )

    return round(
        (10 * weight)
        + (6.25 * height)
        - (5 * age)
        - 161,
        2,
    )


def classify_bmi(bmi):

    if bmi < 18.5:
        return "Underweight"

    elif 18.5 <= bmi < 24.9:
        return "Healthy Weight"

    elif 25 <= bmi < 29.9:
        return "Over Weight"

    return "Obese"


# ============================================================
# Data Processing
# ============================================================

def process_fitness_data(data):
    """
    Prepare fitness prediction input for the trained preprocessor.
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

    # Convert numeric columns
    for column in NUMERIC_FEATURES:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Arrange columns in training order
    df = df[expected_columns]

    # Fill missing values
    df_filled = df.fillna(0)

    logger.debug(
        "Fitness prediction input:\n%s",
        df,
    )

    preprocessor = get_preprocessor()

    return preprocessor.transform(
        df_filled
    )


# ============================================================
# Recommendations
# ============================================================

FITNESS_RECOMMENDATIONS = {

    "Excellent": {
        "status": (
            "Excellent physical fitness has been identified."
        ),
        "recommendations": [
            "Maintain your current exercise routine.",
            "Continue balanced nutrition.",
            "Schedule routine annual health evaluations.",
            "Maintain adequate hydration and sleep.",
        ],
    },

    "Good": {
        "status": (
            "Overall physical fitness is above average."
        ),
        "recommendations": [
            "Continue regular aerobic and strength exercises.",
            "Maintain a healthy body weight.",
            "Monitor cardiovascular health periodically.",
            "Follow a balanced diet.",
        ],
    },

    "Average": {
        "status": (
            "Physical fitness is satisfactory but can be improved."
        ),
        "recommendations": [
            "Increase weekly physical activity.",
            "Include strength training twice weekly.",
            "Improve dietary habits.",
            "Reduce prolonged sedentary behavior.",
        ],
    },

    "Below Average": {
        "status": (
            "Physical fitness is below the recommended level."
        ),
        "recommendations": [
            "Begin a supervised exercise program.",
            "Aim for at least 150 minutes of moderate activity weekly.",
            "Consult a healthcare provider before intensive exercise if necessary.",
            "Focus on gradual weight management.",
        ],
    },

    "Poor": {
        "status": (
            "Physical fitness is significantly reduced."
        ),
        "recommendations": [
            "Consult a physician before beginning an exercise program.",
            "Start with light supervised physical activity.",
            "Address lifestyle risk factors such as obesity and inactivity.",
            "Schedule regular follow-up assessments.",
        ],
    },
}


# ============================================================
# Prediction View
# ============================================================

@login_required
def fitness_calculator(request):

    # --------------------------------------------------------
    # Active patient
    # --------------------------------------------------------

    patient_data = get_active_patient(request)

    if patient_data is None:

        return render(
            request,
            "prediction/fitness/predict.html",
            {
                "form": FitnessForm(),
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
        "Fitness vitals: %s",
        vitals_data,
    )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = FitnessForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # ------------------------------------------------
            # Require vitals
            # ------------------------------------------------

            if vitals_data is None:

                return render(
                    request,
                    "prediction/fitness/predict.html",
                    {
                        "form": form,
                        "error": (
                            "Patient height and weight are "
                            "required before fitness prediction."
                        ),
                    },
                )

            try:

                # ------------------------------------------------
                # Fitness calculations
                # ------------------------------------------------

                BMR = calculate_bmr(
                    vitals_data.weight,
                    vitals_data.height,
                    patient_data.age,
                    patient_data.sex,
                )

                daily_calories = (
                    daily_calories_needed(
                        BMR,
                        patient_data.lifestyle,
                    )
                )

                bmi_category = classify_bmi(
                    vitals_data.BMI
                )

                logger.debug(
                    "Fitness BMR=%s daily_calories=%s BMI_category=%s",
                    BMR,
                    daily_calories,
                    bmi_category,
                )

                # ------------------------------------------------
                # Build prediction input
                # ------------------------------------------------

                data_for_prediction = {
                    "age": patient_data.age,
                    "sex": patient_data.sex,
                    "height": vitals_data.height,
                    "weight": vitals_data.weight,
                    "total_steps": (
                        data["total_steps"]
                    ),
                    "calories_burned": (
                        data["calories_burned"]
                    ),
                    "daily_calories_needed": (
                        daily_calories
                    ),
                    "activity_level": (
                        patient_data.lifestyle
                    ),
                }

                # ------------------------------------------------
                # Preprocess
                # ------------------------------------------------

                input_data = process_fitness_data(
                    data_for_prediction
                )

                # ------------------------------------------------
                # Model inference
                # ------------------------------------------------

                prediction_model = (
                    get_prediction_model()
                )

                prediction = (
                    prediction_model.predict(
                        input_data
                    )
                )

                probability = (
                    prediction_model
                    .predict_proba(input_data)[0][1]
                )

                logger.info(
                    "Fitness prediction=%s probability=%s",
                    prediction[0],
                    probability,
                )

                # ------------------------------------------------
                # Specialized fitness result
                # ------------------------------------------------

                prediction_result = (
                    build_fitness_result(
                        probability,
                        FITNESS_RECOMMENDATIONS,
                            )
                    )


                # ------------------------------------------------
                # Standardized metadata
                # ------------------------------------------------

                prediction_metadata = (
                    generate_prediction_metadata(
                    model_info=MODEL_INFO["fitness"],
                    disease_code="FIT",
                        )
                    )


                # ------------------------------------------------
                # Save through centralized service
                # ------------------------------------------------

                prediction_record, data_quality = (
                    save_prediction_record(
                    patient=patient_data,

                    prediction_type="fitness",

                    prediction=(
                            "Yes"
                            if prediction[0] == 1
                            else "No"
                    ),

                    prediction_data=data_for_prediction,

                    prediction_fields={
                            "BMR": BMR,

                            "daily_calories_needed": (
                                daily_calories
                            ),

                            "total_steps": (
                                data["total_steps"]
                            ),

                            "calories_burned": (
                                data["calories_burned"]
                            ),
                        },

                    standardized_result=prediction_result,

                    prediction_metadata=prediction_metadata,
                            )
                    )
                


                # ------------------------------------------------
                # Render result
                # ------------------------------------------------

                return render(
                    request,
                    "prediction/fitness/result.html",
                    {
                        "patient": patient_data,

                        "prediction_result": (
                            prediction_result
                        ),

                        "data_quality": (
                            data_quality
                        ),

                        "prediction_metadata": (
                            prediction_metadata
                        ),

                        "is_fitness": True,

                        "bmi_category": (
                            bmi_category
                        ),

                        "bmr": BMR,

                        "daily_calories_needed": (
                            daily_calories
                        ),
                    },
                )

            except Exception as e:

                logger.exception(
                    "Error during fitness prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/fitness/predict.html",
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
            "prediction/fitness/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = FitnessForm()

    return render(
        request,
        "prediction/fitness/predict.html",
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
        "prediction/fitness/result.html",
    )