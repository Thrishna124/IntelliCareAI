from collections import Counter

from django.db.models import Count
from django.db.models.functions import TruncMonth

from main_page.models import PatientData, PredictionData


# ==========================================================
# ENTERPRISE ANALYTICS
# ==========================================================

PREDICTION_LABELS = {
    "heart": "Heart Disease",
    "kidney": "Kidney Disease",
    "liver": "Liver Disease",
    "lungs": "Lung Disease",
    "lung_cancer": "Lung Cancer",
    "pancreas": "Diabetes",
    "fitness": "Fitness Risk",
}


def get_analytics_queryset(clinic=None):
    """
    Base prediction queryset for enterprise analytics.

    Optionally restrict analytics to a single clinic.
    """

    queryset = (
        PredictionData.objects
        .select_related(
            "pid",
            "pid__clinic",
        )
        .filter(
            pid__clinic__isnull=False
        )
    )

    if clinic is not None:
        queryset = queryset.filter(
            pid__clinic=clinic
        )

    return queryset


# ==========================================================
# KPI SUMMARY
# ==========================================================

def get_kpi_summary(clinic=None):
    """
    Return top-level enterprise dashboard metrics.
    """

    predictions = get_analytics_queryset(
        clinic=clinic
    )

    patients = PatientData.objects.filter(
        clinic__isnull=False
    )

    if clinic is not None:
        patients = patients.filter(
            clinic=clinic
        )

    total_predictions = predictions.count()

    positive_predictions = predictions.filter(
        prediction="Yes"
    ).count()

    negative_predictions = predictions.filter(
        prediction="No"
    ).count()

    high_risk_patients = (
        predictions
        .filter(prediction="Yes")
        .values("pid_id")
        .distinct()
        .count()
    )

    positive_rate = (
        round(
            (
                positive_predictions
                / total_predictions
            ) * 100,
            1,
        )
        if total_predictions
        else 0
    )

    return {
        "total_patients": patients.count(),
        "total_predictions": total_predictions,
        "positive_predictions": positive_predictions,
        "negative_predictions": negative_predictions,
        "high_risk_patients": high_risk_patients,
        "positive_rate": positive_rate,
    }


# ==========================================================
# DISEASE DISTRIBUTION
# ==========================================================

def get_disease_distribution(clinic=None):
    """
    Return positive prediction counts grouped by module.

    This represents the distribution of detected risk,
    rather than simply the number of times each model ran.
    """

    predictions = (
        get_analytics_queryset(clinic)
        .filter(prediction="Yes")
        .values("prediction_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    results = []

    for item in predictions:

        prediction_type = item[
            "prediction_type"
        ]

        results.append({
            "key": prediction_type,

            "label": PREDICTION_LABELS.get(
                prediction_type,
                prediction_type.replace(
                    "_",
                    " ",
                ).title(),
            ),

            "count": item["count"],
        })

    return results


# ==========================================================
# MODEL EXECUTION DISTRIBUTION
# ==========================================================

def get_prediction_volume_by_type(clinic=None):
    """
    Return total model executions grouped by prediction type.
    """

    predictions = (
        get_analytics_queryset(clinic)
        .values("prediction_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return [
        {
            "key": item["prediction_type"],

            "label": PREDICTION_LABELS.get(
                item["prediction_type"],
                item["prediction_type"]
                .replace("_", " ")
                .title(),
            ),

            "count": item["count"],
        }
        for item in predictions
    ]


# ==========================================================
# MONTHLY PREDICTION TREND
# ==========================================================

def get_monthly_prediction_trend(clinic=None):
    """
    Return prediction volume grouped by calendar month.
    """

    predictions = (
        get_analytics_queryset(clinic)
        .annotate(
            month=TruncMonth("timestamp")
        )
        .values("month")
        .annotate(
            total=Count("id")
        )
        .order_by("month")
    )

    return [
        {
            "month": item["month"].strftime(
                "%b %Y"
            ),
            "total": item["total"],
        }
        for item in predictions
        if item["month"]
    ]


# ==========================================================
# MONTHLY POSITIVE TREND
# ==========================================================

def get_monthly_positive_trend(clinic=None):
    """
    Return positive prediction counts by month.
    """

    predictions = (
        get_analytics_queryset(clinic)
        .filter(prediction="Yes")
        .annotate(
            month=TruncMonth("timestamp")
        )
        .values("month")
        .annotate(
            total=Count("id")
        )
        .order_by("month")
    )

    return [
        {
            "month": item["month"].strftime(
                "%b %Y"
            ),
            "total": item["total"],
        }
        for item in predictions
        if item["month"]
    ]


# ==========================================================
# LIFESTYLE DISTRIBUTION
# ==========================================================

def get_lifestyle_distribution(clinic=None):
    """
    Return patient lifestyle distribution.
    """

    patients = PatientData.objects.filter(
        clinic__isnull=False
    )

    if clinic is not None:
        patients = patients.filter(
            clinic=clinic
        )

    distribution = Counter(
        patients.values_list(
            "lifestyle",
            flat=True,
        )
    )

    return [
        {
            "lifestyle": (
                lifestyle
                .replace("_", " ")
                .title()
                if lifestyle
                else "Unknown"
            ),
            "count": count,
        }
        for lifestyle, count
        in sorted(distribution.items())
    ]


# ==========================================================
# AGE DISTRIBUTION
# ==========================================================

def get_age_distribution(clinic=None):
    """
    Group enterprise patients into useful population-health
    age bands.
    """

    patients = PatientData.objects.filter(
        clinic__isnull=False
    )

    if clinic is not None:
        patients = patients.filter(
            clinic=clinic
        )

    groups = {
        "18-29": 0,
        "30-44": 0,
        "45-59": 0,
        "60-74": 0,
        "75+": 0,
    }

    for age in patients.values_list(
        "age",
        flat=True,
    ):

        if age < 30:
            groups["18-29"] += 1

        elif age < 45:
            groups["30-44"] += 1

        elif age < 60:
            groups["45-59"] += 1

        elif age < 75:
            groups["60-74"] += 1

        else:
            groups["75+"] += 1

    return [
        {
            "group": group,
            "count": count,
        }
        for group, count in groups.items()
    ]

    # ==========================================================
# CLINIC COMPARISON
# ==========================================================

def get_clinic_comparison():
    """
    Compare enterprise analytics across clinics.
    """

    from main_page.models import Clinic

    results = []

    for clinic in Clinic.objects.all():

        patients = PatientData.objects.filter(
            clinic=clinic
        )

        predictions = get_analytics_queryset(
            clinic=clinic
        )

        total_predictions = predictions.count()

        positive_predictions = predictions.filter(
            prediction="Yes"
        ).count()

        high_risk_patients = (
            predictions
            .filter(prediction="Yes")
            .values("pid_id")
            .distinct()
            .count()
        )

        positive_rate = (
            round(
                (
                    positive_predictions
                    / total_predictions
                ) * 100,
                1,
            )
            if total_predictions
            else 0
        )

        results.append({
            "clinic_id": clinic.id,
            "clinic": clinic.name,
            "patients": patients.count(),
            "predictions": total_predictions,
            "positive_predictions": positive_predictions,
            "positive_rate": positive_rate,
            "high_risk_patients": high_risk_patients,
        })

    return results


# ==========================================================
# HIGH-RISK PATIENTS
# ==========================================================

def get_high_risk_patients(
    clinic=None,
    limit=10,
):
    """
    Return patients ranked by positive prediction activity.

    Ranking considers:
    - number of distinct positive AI modules
    - total positive predictions
    - most recent positive assessment
    """

    predictions = (
        get_analytics_queryset(clinic)
        .filter(prediction="Yes")
    )

    patient_data = {}

    for prediction in predictions:

        patient = prediction.pid

        if patient.pk not in patient_data:

            patient_data[patient.pk] = {
                "patient_id": patient.pid,
                "name": " ".join(
                    part
                    for part in [
                        patient.fname,
                        patient.mname,
                        patient.lname,
                    ]
                    if part
                ),
                "clinic": (
                    patient.clinic.name
                    if patient.clinic
                    else "Unknown"
                ),
                "age": patient.age,
                "sex": patient.sex,
                "lifestyle": (
                    patient.lifestyle
                    .replace("_", " ")
                    .title()
                    if patient.lifestyle
                    else "Unknown"
                ),
                "positive_count": 0,
                "positive_modules": set(),
                "latest_positive": None,
            }

        entry = patient_data[
            patient.pk
        ]

        entry[
            "positive_count"
        ] += 1

        entry[
            "positive_modules"
        ].add(
            prediction.prediction_type
        )

        if (
            entry["latest_positive"] is None
            or prediction.timestamp
            > entry["latest_positive"]
        ):
            entry[
                "latest_positive"
            ] = prediction.timestamp

    results = []

    for entry in patient_data.values():

        modules = entry[
            "positive_modules"
        ]

        results.append({
            "patient_id": entry[
                "patient_id"
            ],

            "name": entry["name"],

            "clinic": entry["clinic"],

            "age": entry["age"],

            "sex": entry["sex"],

            "lifestyle": entry[
                "lifestyle"
            ],

            "positive_modules": len(
                modules
            ),

            "modules": sorted(
                PREDICTION_LABELS.get(
                    module,
                    module.replace(
                        "_",
                        " ",
                    ).title(),
                )
                for module in modules
            ),

            "positive_count": entry[
                "positive_count"
            ],

            "latest_positive": entry[
                "latest_positive"
            ],
        })

    results.sort(
        key=lambda item: (
            item["positive_modules"],
            item["positive_count"],
            item["latest_positive"],
        ),
        reverse=True,
    )
    return results[:limit]

def get_gender_distribution(clinic=None):
    """
    Return patient population grouped by sex.
    """

    patients = PatientData.objects.filter(
        clinic__isnull=False
    )

    if clinic is not None:
        patients = patients.filter(
            clinic=clinic
        )

    distribution = (
        patients
        .values("sex")
        .annotate(count=Count("id"))
        .order_by("sex")
    )

    return [
        {
            "label": (
                item["sex"].title()
                if item["sex"]
                else "Unknown"
            ),
            "count": item["count"],
        }
        for item in distribution
    ]