import os
import logging
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect

from .forms import LungCancerPredictionForm
from main_page.models import PredictionData, PatientData, DQScore
from main_page.utils.clinical_workspace import get_active_patient

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------
# Load TensorFlow Models
# --------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "lung_cancer" / "models"

lung_cancer_prediction_model = tf.keras.models.load_model(
    MODEL_DIR / "lung_cancer_normal_model.keras"
)

lung_cancer_diagnosis_model = tf.keras.models.load_model(
    MODEL_DIR / "lung_cancer_model.h5"
)


# --------------------------------------------------------------------
# Create media directory if it doesn't exist
# --------------------------------------------------------------------

def ensure_media_directory():
    media_root = os.path.join(
        settings.MEDIA_ROOT,
        "lung_cancer",
        "data",
        "uploads",
    )

    os.makedirs(media_root, exist_ok=True)

    logger.info(f"Media directory: {media_root}")


# --------------------------------------------------------------------
# Prediction Functions
# --------------------------------------------------------------------

def predict_lung_cancer_fct(img_path):
    try:
        img = image.load_img(img_path, target_size=(150, 150))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        predictions = lung_cancer_prediction_model.predict(img_array)

        return np.argmax(predictions)

    except Exception as e:
        logger.error(f"Error predicting lung cancer: {e}")
        return None


def diagnose_lung_cancer_fct(img_path):
    try:
        img = image.load_img(img_path, target_size=(150, 150))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        diagnosis = lung_cancer_diagnosis_model.predict(img_array)

        return np.argmax(diagnosis)

    except Exception as e:
        logger.error(f"Error diagnosing lung cancer: {e}")
        return None


# --------------------------------------------------------------------
# Prediction View
# --------------------------------------------------------------------

@login_required
def predict_lung_cancer(request):

    patient_data = get_active_patient(request)
    if patient_data is None:
        return render(request, "prediction/lung_cancer/predict.html", {
            "form": LungCancerPredictionForm(),
            "error": "Select a patient from the Clinical Workspace before starting a prediction.",
        })

    if request.method == "POST":

        form = LungCancerPredictionForm(request.POST, request.FILES)

        if form.is_valid():

            ensure_media_directory()

            prediction_instance = form.save(commit=False)
            prediction_instance.pid = patient_data
            prediction_instance.prediction_type = "lung_cancer"
            prediction_instance.save()

            img_path = prediction_instance.image.path

            logger.info(f"Image path: {img_path}")

            if not os.path.exists(img_path):
                logger.error(f"Uploaded image not found: {img_path}")

                return render(
                    request,
                    "prediction/lung_cancer/predict.html",
                    {
                        "form": form,
                        "error": "Uploaded image not found."
                    },
                )

            predicted_class = predict_lung_cancer_fct(img_path)

            class_labels = ["normal", "benign", "malignant"]

            if predicted_class is not None:

                prediction_instance.prediction = (
                    "Yes"
                    if class_labels[predicted_class] in ["benign", "malignant"]
                    else "No"
                )

            diagnosis_class = diagnose_lung_cancer_fct(img_path)

            if diagnosis_class is not None:

                prediction_instance.diagnosis = class_labels[diagnosis_class]

                prediction_instance.save()

                lung_cancer_dq_score = DQScore(
                    prediction_type="lung_cancer",
                    pid=prediction_instance.pid,
                    data_quality_value=100 if os.path.exists(img_path) else 0,
                    total_features_count=1,
                    missing_features_count=0 if os.path.exists(img_path) else 1,
                    missing_features=None if os.path.exists(img_path) else "Image",
                )

                lung_cancer_dq_score.save()

                logger.info(
                    f"Prediction saved for {request.user}: "
                    f"{prediction_instance.diagnosis}"
                )

                return redirect(
                    "lung_cancer:lung_cancer_result",
                    pk=prediction_instance.pk,
                )

            logger.error("Prediction failed.")

            return render(
                request,
                "prediction/lung_cancer/predict.html",
                {
                    "form": form,
                    "error": "Prediction failed. Please try again.",
                },
            )

    else:

        form = LungCancerPredictionForm()

    return render(
        request,
        "prediction/lung_cancer/predict.html",
        {"form": form},
    )


# --------------------------------------------------------------------
# Result View
# --------------------------------------------------------------------

def result(request, pk):

    try:

        prediction_instance = PredictionData.objects.get(pk=pk)

        lung_cancer_dq_score = DQScore.objects.filter(
            pid=prediction_instance.pid,
            prediction_type="lung_cancer",
        ).first()

        if lung_cancer_dq_score:

            missing_features = lung_cancer_dq_score.missing_features

            if isinstance(missing_features, str):

                if missing_features.lower() == "image":
                    missing_features = "Image feature is missing"

                else:
                    missing_features = (
                        "Missing features: " + missing_features
                    )

        else:

            missing_features = "No missing features."

        context = {
            "patient": prediction_instance.pid,
            "prediction": (
                "Might have Lung disorder"
                if prediction_instance.prediction == "Yes"
                else "Do not have any Lung disorder"
            ),
            "diagnosis": prediction_instance.diagnosis,
            "data_quality_report": (
                lung_cancer_dq_score.data_quality_value
                if lung_cancer_dq_score
                else None
            ),
            "missing_columns": missing_features,
        }

        return render(
            request,
            "lung_cancer/result.html",
            context,
        )

    except PredictionData.DoesNotExist:

        logger.error(f"PredictionData {pk} does not exist.")

        return render(
            request,
            "prediction/lung_cancer/predict.html",
            {
                "message": "Prediction not found."
            },
        )
