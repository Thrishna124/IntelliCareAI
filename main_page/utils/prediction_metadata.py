# prediction/utils/prediction_metadata.py

import random
import uuid

from django.utils import timezone


def generate_prediction_metadata(
    disease_code,
    model_info,
    prediction_status="Completed",
):
    """
    Generate standardized metadata for AI prediction reports.
    """

    timestamp = timezone.now()

    return {
        "prediction_id": (
            f"{disease_code}-"
            f"{timestamp:%Y%m%d}-"
            f"{uuid.uuid4().hex[:5].upper()}"
        ),

        # Timestamp
        "generated_on": timestamp,
        "generated_at": timestamp.strftime("%d %b %Y • %I:%M %p"),

        # Report status
        "status": prediction_status,

        # Simulated inference time (replace with actual timing later)
        "processing_time": f"{random.randint(80, 180)} ms",

        # Model details
        "model_info": {
            "model_name": model_info["model_name"],
            "version": model_info["version"],
            "framework": model_info["framework"],
            "prediction_type": model_info["prediction_type"],
            "output": model_info["output"],
            "status": model_info["status"],
        },

        # Audit information
        "audit": {
            "generated_by": "IntelliCareAI",
            "report_version": "2.0",
        },
    }