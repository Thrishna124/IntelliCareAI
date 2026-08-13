"""
Dashboard Context Service

Responsible for building the context required by the
Enterprise Dashboard.
"""

from django.contrib import messages
from django.db.models.functions import TruncSecond

from main_page.models import DQScore, PredictionData
from main_page.utils.clinical_workspace import get_active_patient
from main_page.utils.dashboard_utils import calculate_health_metrics

from .states import DashboardState


# ==========================================================
# Public API
# ==========================================================

def get_dashboard_context(request):
    """
    Build and return the dashboard context.
    """

    context = _default_context()

    patient = get_active_patient(request)

    if patient is None:
        messages.info(
            request,
            "Select a patient from the Clinical Workspace to view their dashboard.",
        )
        return context

    context["patient"] = patient

    prediction_queryset = PredictionData.objects.filter(pid=patient)

    # ------------------------------------------------------
    # No Predictions Yet
    # ------------------------------------------------------

    if not prediction_queryset.exists():

        messages.warning(
            request,
            "No prediction results found."
        )

        context.update({
            "dashboard_state": DashboardState.READY,
            "patient": patient,
        })

        return context

    # ------------------------------------------------------
    # Dashboard Metrics
    # ------------------------------------------------------

    results = _build_dashboard_metrics(
        patient,
        prediction_queryset,
    )

    context.update({
        "dashboard_state": DashboardState.READY,
        "patient": patient,
        "latest_results": [results],
        "prediction_count": results["total_predictions"],
        "health_score": results["health_score"],
        "health_percentage": results["health_percentage"],
        "green_count": results["count_green"],
        "yellow_count": results["count_yellow"],
        "red_count": results["count_red"],
        "health_status": results["health_status"],
        "status_color": results["status_color"],
        "recent_predictions": prediction_queryset.order_by("-timestamp")[:5],
    })

    return context


# ==========================================================
# Dashboard Metrics
# ==========================================================

def _build_dashboard_metrics(patient, prediction_queryset):
    """
    Build dashboard health metrics from prediction data.
    """

    dq_scores = (
        DQScore.objects.filter(pid=patient)
        .annotate(timestamp_rounded=TruncSecond("timestamp"))
        .values(
            "timestamp_rounded",
            "prediction_type",
            "missing_features_count",
            "total_features_count",
        )
    )

    predictions = (
        prediction_queryset
        .annotate(timestamp_rounded=TruncSecond("timestamp"))
        .values(
            "prediction_type",
            "prediction",
            "diagnosis",
            "timestamp",
            "timestamp_rounded",
        )
    )

    best_predictions = {}

    for prediction in predictions:

        dq_score = (
            dq_scores.filter(
                prediction_type=prediction["prediction_type"],
                timestamp_rounded=prediction["timestamp_rounded"],
            )
            .order_by("missing_features_count")
            .first()
        )

        if dq_score is None:
            continue

        disease = prediction["prediction_type"]

        existing = best_predictions.get(disease)

        if (
            existing is None
            or dq_score["missing_features_count"]
            < existing["dq_score"]["missing_features_count"]
        ):
            best_predictions[disease] = {
                "prediction": prediction,
                "dq_score": dq_score,
            }

    return calculate_health_metrics(best_predictions)


# ==========================================================
# Default Context
# ==========================================================

def _default_context():
    """
    Default dashboard context before a patient is selected.
    """

    return {
        "dashboard_state": DashboardState.NO_PATIENT,
        "patient": None,
        "latest_results": [],
        "prediction_count": 0,
        "health_score": 0,
        "health_percentage": 0,
        "green_count": 0,
        "yellow_count": 0,
        "red_count": 0,
        "recent_predictions": [],
        "health_status": "No Patient Selected",
        "status_color": "secondary",
    }