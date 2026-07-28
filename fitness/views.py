########## Import Statements ##########

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from fitness.forms import FitnessForm

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
def get_fitness_prediction_model():
    return joblib.load(MODEL_DIR / "fitness_model.pkl")

@lru_cache(maxsize=1)
def get_fitness_preprocessor():
    return joblib.load(MODEL_DIR / "fitness_preprocessor.pkl")

NUMERIC_FEATURES = [
    'age', 
    'height',
    'weight', 
    'total_steps', 
    'calories_burned', 
    'daily_calories_needed'
]

CATEGORICAL_FEATURES = [
    "sex",
    'activity_level'
]

def daily_calories_needed(bmr, activity_level):
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'super_active': 1.9
    }
    return round(bmr * activity_multipliers.get(activity_level, 1.2), 2)

def calculate_bmr(weight, height, age, gender):
    if gender == 'Male':
        return round((10 * weight) + (6.25 * height) - (5 * age) + 5, 2)
    else:
        return round((10 * weight) + (6.25 * height) - (5 * age) - 161, 2)
    

def classify_bmi(bmi):
    if bmi < 18.5:
        return 'Underweight'
    elif 18.5 <= bmi < 24.9:
        return 'Healthy Weight'
    elif 25 <= bmi < 29.9:
        return 'Over Weight'
    else:
        return 'Obese'


def process_fitness_data(data):
    """
    Prepare fitness prediction input for the trained preprocessor.
    """
    # Convert the input data (which is likely a dictionary) to a DataFrame
    df = pd.DataFrame([data])

    # Ensure all expected columns exist, adding missing ones as NA
    expected_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    for col in expected_columns:
        if col not in df.columns:
            df[col] = pd.NA

    # Convert numeric columns to the correct type
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Select only the expected columns (in the correct order)
    df = df[expected_columns]
    # Fill missing values
    df_filled = df.fillna(0)
    # Apply the preprocessor (e.g., one-hot encoding, scaling, etc.)
    logger.debug("Fitness prediction input:\n%s", df)

    preprocessor = get_fitness_preprocessor()
    
    return preprocessor.transform(df_filled)


@login_required
def fitness_calculator(request):
    patient_data = get_active_patient(request)
    if patient_data is None:
        return render(request, "prediction/fitness/predict.html", {
            "form": FitnessForm(),
            "error": "Select a patient from the Clinical Workspace before starting a prediction.",
        })
    vitals_data = FormVitals.objects.filter(pid=patient_data).order_by('-id').first()

    logger.debug(f"Vitals Data: {vitals_data}")

    if request.method == 'POST':
        form = FitnessForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if not vitals_data:  # Ensure vitals_data is present
                logger.error("No vitals data found.")
                return render(request, 'fitness/predict.html', {'form': form, 'error': 'No vitals data found.'})

            try:
                # Prepare data for prediction
                BMR = calculate_bmr(vitals_data.weight, vitals_data.height, patient_data.age, patient_data.sex)
                daily_calories = daily_calories_needed(BMR, patient_data.lifestyle)
                bmi_category = classify_bmi(vitals_data.BMI)

                data_for_prediction = {
                    'age': patient_data.age,
                    'sex': patient_data.sex,
                    'height': vitals_data.height,
                    'weight': vitals_data.weight,
                    'total_steps': data['total_steps'],
                    'calories_burned': data['calories_burned'],
                    'daily_calories_needed': daily_calories,
                    'activity_level':patient_data.lifestyle
                }

                # Preprocess the input data
                input_data_transformed = process_fitness_data(data_for_prediction)

                # Predict fitness status
                prediction_model = get_fitness_prediction_model()

                prediction = prediction_model.predict(input_data_transformed)

                # Save data to the PredictionData table
                prediction_result = PredictionData(
                    BMR=BMR,
                    daily_calories_needed=daily_calories,
                    total_steps=data['total_steps'],
                    calories_burned=data['calories_burned'],
                    prediction='Yes' if prediction[0] == 1 else 'No',
                    prediction_type='fitness',
                    pid=patient_data
                )
                with transaction.atomic():
                    prediction_result.save()
                    fitness_dq_score = save_dq_score(
                    prediction_type='fitness',
                    pid=patient_data,
                    prediction_data = data_for_prediction)
                
                context = {
                    'BMI': vitals_data.BMI,
                    'bmi_category':bmi_category,
                    'BMR': BMR,
                    'Daily_Calories': daily_calories,
                    'Fitness_Prediction': 'Good Fitness Score' if prediction[0] == 1 else 'Fitness score is low',
                    'data_quality_report' : fitness_dq_score.data_quality_value,
                    'missing_columns' : fitness_dq_score.missing_features
                }

                return render(request, 'fitness/result.html', context)

            except Exception as e:
                logger.error("Error during calculations or saving data")
                return render(request, 'prediction/fitness/predict.html', {'form': form, "error_message": (
                            "An error occurred during prediction. "
                            "Please try again."
                        ),})

    else:
        form = FitnessForm()

    return render(request, 'prediction/fitness/predict.html', {'form': form})


def result(request):
    return render(request, 'fitness/result.html')
