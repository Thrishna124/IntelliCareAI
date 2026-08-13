import uuid

from django.utils import timezone


def generate_prediction_metadata(
    disease_code,
    model_info,
    prediction_status="Completed",
):
    """
    Generate standardized metadata for AI prediction reports.

    Supports the existing MODEL_INFO structure while providing
    a consistent metadata contract for all prediction modules.
    """

    timestamp = timezone.now()

    # ----------------------------------------------------------
    # Backward-compatible model information
    # ----------------------------------------------------------

    model_name = model_info.get(
        "model_name",
        model_info.get(
            "algorithm",
            "AI Prediction Model",
        ),
    )

    version = model_info.get(
        "version",
        "1.0",
    )

    framework = model_info.get(
        "framework",
        "Machine Learning",
    )

    prediction_type = model_info.get(
        "prediction_type",
        disease_code,
    )

    output = model_info.get(
        "output",
        "Risk prediction",
    )

    status = model_info.get(
        "status",
        "Active",
    )

    # ----------------------------------------------------------
    # Prediction metadata
    # ----------------------------------------------------------

    return {
        "prediction_id": (
            f"{disease_code}-"
            f"{timestamp:%Y%m%d}-"
            f"{uuid.uuid4().hex[:5].upper()}"
        ),

        # Timestamp
        "generated_on": timestamp,

        "generated_at": (
            timestamp.strftime(
                "%d %b %Y • %I:%M %p"
            )
        ),

        # Report status
        "status": prediction_status,

        # Processing time
        #
        # This remains a placeholder for now.
        # Phase 4 will later replace this with
        # actual model inference timing.
        "processing_time": "N/A",

        # Model details
        "model_info": {
            "model_name": model_name,
            "version": version,
            "framework": framework,
            "prediction_type": prediction_type,
            "output": output,
            "status": status,

            # Preserve existing model information
            # for future analytics/reporting.
            "algorithm": model_info.get(
                "algorithm",
                model_name,
            ),

            "accuracy": model_info.get(
                "accuracy",
                None,
            ),

            "dataset": model_info.get(
                "dataset",
                None,
            ),

            "features": model_info.get(
                "features",
                None,
            ),
        },

        # Audit information
        "audit": {
            "generated_by": "IntelliCareAI",
            "report_version": "2.0",
        },
    }