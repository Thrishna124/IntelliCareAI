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
    dq = DQScore(
        prediction_type=prediction_type,
        pid=patient,
        data_quality_value=dq_score,
        total_features_count=len(prediction_data),
        missing_features_count=len(missing_features),
        missing_features=", ".join(missing_features),
    )

    EXCELLENT_THRESHOLD = 90
    GOOD_THRESHOLD = 75

    if dq_score >= EXCELLENT_THRESHOLD:
        dq.status = "Excellent"
        dq.badge = "success"

    elif dq_score >= GOOD_THRESHOLD:
        dq.status = "Good"
        dq.badge = "warning"

    else:
        dq.status = "Needs Review"
        dq.badge = "danger"

    # Presentation helper (not stored in DB)
    dq.missing_features_list = missing_features

    return dq

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
