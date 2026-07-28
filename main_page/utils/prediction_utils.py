"""
Shared utility functions for IntelliCareAI prediction modules.

These helpers are used by all ML prediction apps
(Heart, Kidney, Liver, Lung, Pancreas, Fitness, Stroke, etc.)
to calculate data quality metrics and create DQScore records.
"""

import logging

from main_page.models import DQScore

logger = logging.getLogger(__name__)


def missing_data(data):
    """
    Return a list of fields with missing values.
    """
    return [
        key
        for key, value in data.items()
        if value in (None, "", "None")
    ]


def data_quality_percentage(data):
    """
    Calculate percentage of available values.
    """
    valid_count = sum(
        value not in (None, "", "None")
        for value in data.values()
    )

    total = len(data)

    if total == 0:
        return 0

    return round((valid_count / total) * 100, 1)


def create_dq_score(
    prediction_type,
    patient,
    prediction_data,
):
    """
    Create an unsaved DQScore object.
    """

    missing_features = missing_data(prediction_data)
    dq_score = data_quality_percentage(prediction_data)
    return DQScore(
        prediction_type=prediction_type,
        pid=patient,
        data_quality_value=dq_score,
        total_features_count=len(prediction_data),
        missing_features_count=len(missing_features),
        missing_features=", ".join(missing_features),
    )

def save_dq_score(
    prediction_type,
    patient,
    prediction_data,
):
    """
    Create and save a DQScore object.

    Returns the saved DQScore instance.
    """

    dq = create_dq_score(
        prediction_type=prediction_type,
        patient=patient,
        prediction_data=prediction_data,
    )

    try:
        dq.save()
    except Exception:
        logger.exception("Unable to save DQScore.")
        raise

    return dq


def build_prediction_result(probability, disease_name, recommendation_map):
    """
    Returns:
        prediction
        risk_level
        risk_percentage
        recommendations
    """

    risk_percentage = round(probability * 100, 1)

    RISK_THRESHOLDS = (
    (20, "Very Low"),
    (40, "Low"),
    (60, "Borderline"),
    (80, "Moderate"),
)
    risk_level = "High"

    for limit, level in RISK_THRESHOLDS:
        if risk_percentage < limit:
            risk_level = level
        break

    prediction = f"{risk_level} likelihood of {disease_name.lower()}."

    recommendations = recommendation_map.get(risk_level, [])

    return {
    "prediction": prediction,
    "risk_level": risk_level,
    "risk_percentage": risk_percentage,
    "recommendations": recommendations,
    # Future additions

    "clinical_priority": risk_level,

    "confidence_score": risk_percentage,

    "follow_up": None,

    "follow_up_days": None,
}