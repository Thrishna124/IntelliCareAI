import logging

from django.db import transaction

from main_page.models import PredictionData
from main_page.utils.prediction_utils import (
    save_dq_score,
    build_prediction_result,
)
from main_page.utils.prediction_metadata import (
    generate_prediction_metadata,
)

logger = logging.getLogger(__name__)


def save_prediction_record(
    *,
    patient,
    prediction_type,
    prediction,
    prediction_data,
    prediction_fields=None,
    diagnosis=None,
):
    """
    Save a standardized prediction record and its data-quality score.

    This service handles the common persistence layer used by
    IntelliCareAI prediction modules.

    Parameters
    ----------
    patient:
        PatientData instance.

    prediction_type:
        PredictionTypeChoices value.

    prediction:
        General prediction result, usually "Yes" or "No".

    prediction_data:
        Dictionary containing the input features used by the model.

    prediction_fields:
        Additional fields to store in PredictionData.

    diagnosis:
        Optional diagnosis/classification.

    Returns
    -------
    tuple
        (PredictionData instance, DQScore instance)
    """

    prediction_fields = prediction_fields or {}

    record_data = {
        "pid": patient,
        "prediction_type": prediction_type,
        "prediction": prediction,
    }

    if diagnosis is not None:
        record_data["diagnosis"] = diagnosis

    record_data.update(prediction_fields)

    with transaction.atomic():

        prediction_record = PredictionData(
            **record_data
        )

        prediction_record.save()

        data_quality = save_dq_score(
            prediction_type=prediction_type,
            patient=patient,
            prediction_data=prediction_data,
        )

    logger.info(
        "Prediction saved successfully: type=%s patient=%s record=%s",
        prediction_type,
        patient.pid,
        prediction_record.pk,
    )

    return prediction_record, data_quality


def build_standard_prediction(
    *,
    probability,
    disease_name,
    recommendation_map,
):
    """
    Build the standardized clinical prediction result.

    This delegates risk classification and recommendations
    to the existing prediction utility layer.
    """

    return build_prediction_result(
        probability=probability,
        disease_name=disease_name,
        recommendation_map=recommendation_map,
    )


def build_prediction_metadata(
    *,
    model_info,
    disease_code,
    prediction_status="Completed",
):
    """
    Generate standardized metadata for a prediction report.
    """

    return generate_prediction_metadata(
        disease_code=disease_code,
        model_info=model_info,
        prediction_status=prediction_status,
    )


def execute_standard_prediction(
    *,
    patient,
    prediction_type,
    probability,
    disease_name,
    recommendation_map,
    prediction_data,
    prediction,
    model_info,
    disease_code,
    prediction_fields=None,
    diagnosis=None,
):
    """
    Complete standardized workflow for a tabular prediction.

    Workflow:

        1. Save PredictionData
        2. Calculate/save DQScore
        3. Build standardized prediction result
        4. Generate prediction metadata

    Model inference itself remains inside the individual
    prediction module because each ML model has its own
    preprocessing and inference requirements.
    """

    prediction_record, data_quality = save_prediction_record(
        patient=patient,
        prediction_type=prediction_type,
        prediction=prediction,
        prediction_data=prediction_data,
        prediction_fields=prediction_fields,
        diagnosis=diagnosis,
    )

    prediction_result = build_standard_prediction(
        probability=probability,
        disease_name=disease_name,
        recommendation_map=recommendation_map,
    )

    prediction_metadata = build_prediction_metadata(
        model_info=model_info,
        disease_code=disease_code,
    )

    return {
        "prediction_record": prediction_record,
        "data_quality": data_quality,
        "prediction_result": prediction_result,
        "prediction_metadata": prediction_metadata,
    }