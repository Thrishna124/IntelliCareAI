import os
import logging
from pathlib import Path

import numpy as np
import tensorflow as tf

from tensorflow.keras.preprocessing import image

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import LungCancerPredictionForm

from main_page.models import PredictionData

from main_page.services.prediction_service import (
    execute_standard_prediction,
)

from main_page.utils.clinical_workspace import (
    get_active_patient,
)

from main_page.utils.model_info import (
    MODEL_INFO,
)

from main_page.utils.prediction_utils import (
    build_prediction_result,
)

from main_page.utils.prediction_metadata import (
    generate_prediction_metadata,
)

from lung_cancer.clinical_interpretation import (
    LUNG_CANCER_INTERPRETATION,
)

from lung_cancer.recommendations import (
    LUNG_CANCER_RECOMMENDATIONS,
)


logger = logging.getLogger(__name__)


# ============================================================
# Model Paths
# ============================================================

MODEL_DIR = Path(__file__).resolve().parent / "models"

# ============================================================
# Lazy TensorFlow Model Loading
# ============================================================

lung_cancer_prediction_model = None
lung_cancer_diagnosis_model = None


def get_lung_cancer_prediction_model():
    """
    Load the lung cancer prediction model only when required.
    """

    global lung_cancer_prediction_model

    if lung_cancer_prediction_model is None:

        logger.info(
            "Loading lung cancer prediction model..."
        )

        lung_cancer_prediction_model = (
            tf.keras.models.load_model(
                MODEL_DIR / "lung_cancer_normal_model.keras"
            )
        )

        logger.info(
            "Lung cancer prediction model loaded successfully."
        )

    return lung_cancer_prediction_model


def get_lung_cancer_diagnosis_model():
    """
    Load the lung cancer diagnosis model only when required.
    """

    global lung_cancer_diagnosis_model

    if lung_cancer_diagnosis_model is None:

        logger.info(
            "Loading lung cancer diagnosis model..."
        )

        lung_cancer_diagnosis_model = (
            tf.keras.models.load_model(
                MODEL_DIR / "lung_cancer_model.h5"
            )
        )

        logger.info(
            "Lung cancer diagnosis model loaded successfully."
        )

    return lung_cancer_diagnosis_model

# ============================================================
# Media Directory
# ============================================================

def ensure_media_directory():

    media_root = os.path.join(
        settings.MEDIA_ROOT,
        "lung_cancer",
        "data",
        "uploads",
    )

    os.makedirs(
        media_root,
        exist_ok=True,
    )

    logger.info(
        "Lung Cancer media directory: %s",
        media_root,
    )


# ============================================================
# Image Processing
# ============================================================

def process_lung_cancer_image(img_path):
    """
    Prepare the uploaded image for the trained
    Lung Cancer TensorFlow models.
    """

    img = image.load_img(
        img_path,
        target_size=(150, 150),
    )

    img_array = image.img_to_array(
        img
    )

    img_array = np.expand_dims(
        img_array,
        axis=0,
    )

    img_array = img_array / 255.0

    return img_array


# ============================================================
# Lung Cancer Prediction Model
# ============================================================

def predict_lung_cancer_fct(img_path):
    """
    Run the Lung Cancer prediction model.

    Returns:
        predicted_class
        class probabilities
    """

    try:

        input_data = (
            process_lung_cancer_image(
                img_path
            )
        )

        predictions = (
            get_lung_cancer_prediction_model().predict(
                input_data,
                verbose=0,
            )
        )

        predicted_class = int(
            np.argmax(
                predictions[0]
            )
        )

        probabilities = predictions[0]

        return (
            predicted_class,
            probabilities,
        )

    except Exception as e:

        logger.exception(
            "Error predicting lung cancer: %s",
            e,
        )

        return None, None


# ============================================================
# Lung Cancer Diagnosis Model
# ============================================================

def diagnose_lung_cancer_fct(img_path):
    """
    Run the Lung Cancer diagnosis model.

    Returns:
        diagnosis class
        diagnosis probabilities
    """

    try:

        input_data = (
            process_lung_cancer_image(
                img_path
            )
        )

        diagnosis_predictions = (
            get_lung_cancer_diagnosis_model().predict(
                input_data,
                verbose=0,
            )
        )

        diagnosis_class = int(
            np.argmax(
                diagnosis_predictions[0]
            )
        )

        diagnosis_probabilities = (
            diagnosis_predictions[0]
        )

        return (
            diagnosis_class,
            diagnosis_probabilities,
        )

    except Exception as e:

        logger.exception(
            "Error diagnosing lung cancer: %s",
            e,
        )

        return None, None


# ============================================================
# Prediction View
# ============================================================

@login_required
def predict_lung_cancer(request):

    patient_data = get_active_patient(
        request
    )

    # --------------------------------------------------------
    # Active patient required
    # --------------------------------------------------------

    if patient_data is None:

        return render(
            request,
            "prediction/lung_cancer/predict.html",
            {
                "form": (
                    LungCancerPredictionForm()
                ),
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

        form = LungCancerPredictionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            try:

                # ------------------------------------------------
                # Prepare upload directory
                # ------------------------------------------------

                ensure_media_directory()

                uploaded_image = (
                    form.cleaned_data["image"]
                )

                if not uploaded_image:

                    return render(
                        request,
                        "prediction/lung_cancer/predict.html",
                        {
                            "form": form,
                            "error": (
                                "Please upload a lung image."
                            ),
                        },
                    )

                # ------------------------------------------------
                # Temporary image path
                #
                # The image must exist on disk before TensorFlow
                # processes it.
                # ------------------------------------------------

                upload_dir = os.path.join(
                    settings.MEDIA_ROOT,
                    "lung_cancer",
                    "data",
                    "uploads",
                )

                os.makedirs(
                    upload_dir,
                    exist_ok=True,
                )

                temp_image_path = os.path.join(
                    upload_dir,
                    uploaded_image.name,
                )

                with open(
                    temp_image_path,
                    "wb+",
                ) as destination:

                    for chunk in uploaded_image.chunks():

                        destination.write(chunk)

                logger.info(
                    "Lung Cancer image saved temporarily: %s",
                    temp_image_path,
                )

                # ------------------------------------------------
                # Class Labels
                # ------------------------------------------------

                class_labels = [
                    "normal",
                    "benign",
                    "malignant",
                ]

                # ------------------------------------------------
                # Prediction Model
                # ------------------------------------------------

                (
                    predicted_class,
                    probabilities,
                ) = predict_lung_cancer_fct(
                    temp_image_path
                )

                if (
                    predicted_class is None
                    or probabilities is None
                ):

                    logger.error(
                        "Lung Cancer prediction failed."
                    )

                    return render(
                        request,
                        "prediction/lung_cancer/predict.html",
                        {
                            "form": form,
                            "error": (
                                "Prediction failed. "
                                "Please try again."
                            ),
                        },
                    )

                # ------------------------------------------------
                # Diagnosis Model
                # ------------------------------------------------

                (
                    diagnosis_class,
                    diagnosis_probabilities,
                ) = diagnose_lung_cancer_fct(
                    temp_image_path
                )

                if (
                    diagnosis_class is None
                    or diagnosis_probabilities is None
                ):

                    logger.error(
                        "Lung Cancer diagnosis failed."
                    )

                    return render(
                        request,
                        "prediction/lung_cancer/predict.html",
                        {
                            "form": form,
                            "error": (
                                "Diagnosis failed. "
                                "Please try again."
                            ),
                        },
                    )

                diagnosis = class_labels[
                    diagnosis_class
                ]

                # ------------------------------------------------
                # Diagnosis Confidence
                # ------------------------------------------------

                diagnosis_confidence = round(
                    float(
                        diagnosis_probabilities[
                            diagnosis_class
                        ]
                    )
                    * 100,
                    1,
                )

                # ------------------------------------------------
                # Malignant Probability
                # ------------------------------------------------

                malignant_probability = float(
                    probabilities[2]
                )

                logger.info(
                    "Lung Cancer prediction=%s",
                    class_labels[
                        predicted_class
                    ],
                )

                logger.info(
                    "Lung Cancer diagnosis=%s confidence=%s%%",
                    diagnosis,
                    diagnosis_confidence,
                )

                logger.info(
                    "Malignant probability=%s",
                    malignant_probability,
                )

                # ------------------------------------------------
                # Clinical Interpretation
                # ------------------------------------------------

                clinical_interpretation = (
                    LUNG_CANCER_INTERPRETATION
                    .get(
                        diagnosis,
                        {},
                    )
                    .get(
                        "description",
                        "",
                    )
                )

                # ------------------------------------------------
                # Centralized Prediction Workflow
                # ------------------------------------------------

                prediction_workflow = (
                    execute_standard_prediction(
                        patient=patient_data,

                        prediction_type=(
                            "lung_cancer"
                        ),

                        probability=(
                            malignant_probability
                        ),

                        disease_name=(
                            "Lung Cancer"
                        ),

                        recommendation_map=(
                            LUNG_CANCER_RECOMMENDATIONS
                        ),

                        prediction_data={
                            "image": (
                                uploaded_image.name
                            ),
                        },

                        prediction=(
                            "Yes"
                            if class_labels[
                                predicted_class
                            ] == "malignant"
                            else "No"
                        ),

                        model_info=MODEL_INFO[
                            "lung_cancer"
                        ],

                        disease_code="LCA",

                        prediction_fields={
                            "image": uploaded_image,
                        },

                        diagnosis=diagnosis,
                    )
                )

                # ------------------------------------------------
                # Render Result
                # ------------------------------------------------

                return render(
                    request,
                    "prediction/lung_cancer/result.html",
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

                        "prediction_id": (
                            prediction_workflow[
                                "prediction_record"
                            ].pk
                        ),

                        "is_fitness": False,
                    },
                )

            except Exception as e:

                logger.exception(
                    "Error during Lung Cancer prediction: %s",
                    e,
                )

                return render(
                    request,
                    "prediction/lung_cancer/predict.html",
                    {
                        "form": form,
                        "error": (
                            "An error occurred during "
                            "Lung Cancer prediction. "
                            "Please check the server logs."
                        ),
                    },
                )

        # --------------------------------------------------------
        # Invalid Form
        # --------------------------------------------------------

        return render(
            request,
            "prediction/lung_cancer/predict.html",
            {
                "form": form,
            },
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    form = LungCancerPredictionForm()

    return render(
        request,
        "prediction/lung_cancer/predict.html",
        {
            "form": form,
        },
    )


# ============================================================
# Result View
# ============================================================

@login_required
def result(request, pk):

    try:

        prediction_instance = (
            PredictionData.objects.get(
                pk=pk
            )
        )

        return render(
            request,
            "prediction/lung_cancer/result.html",
            {
                "patient": (
                    prediction_instance.pid
                ),

                "diagnosis": (
                    prediction_instance.diagnosis
                ),

                "is_fitness": False,
            },
        )

    except PredictionData.DoesNotExist:

        logger.error(
            "PredictionData %s does not exist.",
            pk,
        )

        return render(
            request,
            "prediction/lung_cancer/predict.html",
            {
                "message": (
                    "Prediction not found."
                ),
            },
        )