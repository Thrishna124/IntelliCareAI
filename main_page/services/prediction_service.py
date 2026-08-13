import logging

from django.db import transaction

from main_page.models import (
    PredictionData,
    PredictionResult,
)

from main_page.utils.prediction_utils import (
    save_dq_score,
    build_prediction_result,
)

from main_page.utils.prediction_metadata import (
    generate_prediction_metadata,
)


logger = logging.getLogger(__name__)


# ============================================================
# Save Prediction Record
# ============================================================

def save_prediction_record(
    *,
    patient,
    prediction_type,
    prediction,
    prediction_data,
    prediction_fields=None,
    diagnosis=None,
    standardized_result=None,
    prediction_metadata=None,
):
    """
    Save the standardized prediction record, DQ score,
    and optional standardized PredictionResult.

    Existing callers that do not provide standardized_result
    and prediction_metadata remain fully supported.

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

        # ----------------------------------------------------
        # PredictionData
        # ----------------------------------------------------

        prediction_record = PredictionData(
            **record_data
        )

        prediction_record.save()


        # ----------------------------------------------------
        # Data Quality Score
        # ----------------------------------------------------

        data_quality = save_dq_score(
            prediction_type=prediction_type,
            patient=patient,
            prediction_data=prediction_data,
        )


        # ----------------------------------------------------
        # Standardized PredictionResult
        # ----------------------------------------------------

        if (
            standardized_result is not None
            and prediction_metadata is not None
        ):

            save_prediction_result(
                prediction_record=prediction_record,
                prediction_result=standardized_result,
                prediction_metadata=prediction_metadata,
            )


    logger.info(
        "Prediction saved successfully: "
        "type=%s patient=%s record=%s",
        prediction_type,
        patient.pid,
        prediction_record.pk,
    )

    return prediction_record, data_quality


# ============================================================
# Save Prediction Result
# ============================================================

def save_prediction_result(
    *,
    prediction_record,
    prediction_result,
    prediction_metadata,
):
    """
    Persist the standardized AI prediction result.

    PredictionResult is linked one-to-one with PredictionData.
    """

    model_info = prediction_metadata.get(
        "model_info",
        {},
    )

    audit_info = prediction_metadata.get(
        "audit",
        {},
    )

    result = PredictionResult(
        prediction=prediction_record,

        # ----------------------------------------------------
        # Standardized prediction output
        # ----------------------------------------------------

        prediction_text=prediction_result.get(
            "prediction",
            "",
        ),

        risk_level=prediction_result.get(
            "risk_level",
            "",
        ),

        risk_percentage=prediction_result.get(
            "risk_percentage",
            None,
        ),

        confidence_score=prediction_result.get(
            "confidence_score",
            None,
        ),

        clinical_priority=prediction_result.get(
            "clinical_priority",
            "",
        ),

        status=prediction_result.get(
            "status",
            "",
        ),

        recommendations=prediction_result.get(
            "recommendations",
            [],
        ),

        follow_up=prediction_result.get(
            "follow_up",
            None,
        ),

        follow_up_days=prediction_result.get(
            "follow_up_days",
            None,
        ),

        # ----------------------------------------------------
        # Report metadata
        # ----------------------------------------------------

        report_id=prediction_metadata.get(
            "prediction_id",
        ),

        generated_on=prediction_metadata.get(
            "generated_on",
        ),

        generated_at=prediction_metadata.get(
            "generated_at",
            "",
        ),

        processing_time=prediction_metadata.get(
            "processing_time",
            "",
        ),

        # ----------------------------------------------------
        # AI model metadata
        # ----------------------------------------------------

        model_metadata=model_info,

        audit_metadata=audit_info,
    )

    result.save()

    logger.info(
        "PredictionResult saved: "
        "prediction=%s result=%s report_id=%s",
        prediction_record.pk,
        result.pk,
        result.report_id,
    )

    return result


# ============================================================
# Build Standard Prediction
# ============================================================

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


# ============================================================
# Build Prediction Metadata
# ============================================================

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


# ============================================================
# Execute Standard Prediction
# ============================================================

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

        1. Build standardized prediction result
        2. Generate prediction metadata
        3. Save PredictionData
        4. Save DQScore
        5. Save PredictionResult

    All persistence operations occur inside the same
    database transaction.

    Model inference itself remains inside the individual
    prediction module because each ML model has its own
    preprocessing and inference requirements.
    """

    # --------------------------------------------------------
    # Build standardized result
    # --------------------------------------------------------

    prediction_result = build_standard_prediction(
        probability=probability,
        disease_name=disease_name,
        recommendation_map=recommendation_map,
    )


    # --------------------------------------------------------
    # Generate standardized metadata
    # --------------------------------------------------------

    prediction_metadata = build_prediction_metadata(
        model_info=model_info,
        disease_code=disease_code,
    )


    # --------------------------------------------------------
    # Persist everything together
    # --------------------------------------------------------

    prediction_record, data_quality = save_prediction_record(
        patient=patient,

        prediction_type=prediction_type,

        prediction=prediction,

        prediction_data=prediction_data,

        prediction_fields=prediction_fields,

        diagnosis=diagnosis,

        standardized_result=prediction_result,

        prediction_metadata=prediction_metadata,
    )


    # --------------------------------------------------------
    # Return standardized workflow
    # --------------------------------------------------------

    return {
        "prediction_record": prediction_record,

        "data_quality": data_quality,

        "prediction_result": prediction_result,

        "prediction_metadata": prediction_metadata,
    }
