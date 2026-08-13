import random
from collections import Counter

from django.db import transaction

from main_page.models import PatientData, PredictionData

from .config import DEMO_CONFIG

from .helpers.date_helper import (
    generate_historical_dates,
    generate_followup_date,
    random_prediction_count,
)

from .helpers.prediction_helper import (
    build_patient_health_profile,
    calculate_disease_risks,
    generate_prediction_outcome,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

PREDICTION_TYPES = (
    "heart",
    "kidney",
    "liver",
    "lungs",
    "lung_cancer",
    "pancreas",
    "fitness",
)


def _history_count_for_risk(risk_score):
    """
    Determine how many historical assessments a patient
    receives for a prediction module.

    Higher-risk patients tend to receive more follow-ups.
    """

    base_count = random_prediction_count(
        minimum=1,
        maximum=4,
    )

    if risk_score >= 0.70:
        base_count += random.choice([1, 1, 2])

    elif risk_score >= 0.50:
        base_count += random.choice([0, 1])

    return min(base_count, 5)


def _build_module_history(
    patient,
    prediction_type,
    base_risk,
    months_back,
):
    """
    Build historical PredictionData objects for one patient
    and one prediction module.

    Risk varies slightly between visits while remaining
    correlated with the patient's persistent health profile.
    """

    count = _history_count_for_risk(
        base_risk
    )

    dates = generate_historical_dates(
        count=count,
        months_back=months_back,
    )

    records = []

    current_risk = base_risk

    for index, prediction_date in enumerate(dates):

        # Earlier/later assessments should not be identical.
        visit_variation = random.uniform(
            -0.07,
            0.07,
        )

        # Small longitudinal drift creates believable trends.
        drift = index * random.uniform(
            -0.015,
            0.025,
        )

        visit_risk = (
            current_risk
            + visit_variation
            + drift
        )

        visit_risk = max(
            0.005,
            min(visit_risk, 0.95),
        )

        outcome = generate_prediction_outcome(
            prediction_type,
            visit_risk,
        )

        records.append(
            PredictionData(
                pid=patient,
                prediction_type=prediction_type,
                prediction=outcome["prediction"],
                diagnosis=outcome["diagnosis"],
                timestamp=prediction_date,
            )
        )

    return records


def build_prediction_history():
    """
    Build prediction history in memory.

    No database changes occur here.

    Returns:
        records:
            List of unsaved PredictionData objects.

        summary:
            Statistics describing the generated dataset.
    """

    seed = DEMO_CONFIG.get(
        "random_seed",
        42,
    )

    random.seed(seed)

    months_back = DEMO_CONFIG.get(
        "prediction_history_months",
        18,
    )

    patients = (
        PatientData.objects
        .select_related("clinic")
        .all()
    )

    records = []

    type_counts = Counter()
    outcome_counts = Counter()
    clinic_counts = Counter()

    for patient in patients:

        # IMPORTANT:
        # Build once per patient so their synthetic health
        # characteristics remain consistent across modules.
        profile = build_patient_health_profile(
            patient
        )

        risks = calculate_disease_risks(
            profile
        )

        for prediction_type in PREDICTION_TYPES:

            base_risk = risks[
                prediction_type
            ]

            module_records = _build_module_history(
                patient=patient,
                prediction_type=prediction_type,
                base_risk=base_risk,
                months_back=months_back,
            )

            records.extend(
                module_records
            )

            for record in module_records:

                type_counts[
                    record.prediction_type
                ] += 1

                outcome_counts[
                    record.prediction
                ] += 1

                clinic_counts[
                    patient.clinic.name
                ] += 1

    summary = {
        "patients": patients.count(),
        "total": len(records),
        "types": type_counts,
        "outcomes": outcome_counts,
        "clinics": clinic_counts,
    }

    return records, summary


def print_prediction_summary(summary):
    """
    Print a readable summary of generated demo history.
    """

    print("\n" + "=" * 60)
    print("INTELLICAREAI PREDICTION HISTORY")
    print("=" * 60)

    print(
        f"\nPatients processed: "
        f"{summary['patients']}"
    )

    print(
        f"Predictions prepared: "
        f"{summary['total']}"
    )

    print("\nPrediction Types")
    print("-" * 60)

    for prediction_type, count in sorted(
        summary["types"].items()
    ):
        print(
            f"{prediction_type:<20} "
            f"{count:>6}"
        )

    print("\nOutcomes")
    print("-" * 60)

    for outcome, count in sorted(
        summary["outcomes"].items()
    ):
        print(
            f"{outcome:<20} "
            f"{count:>6}"
        )

    print("\nClinics")
    print("-" * 60)

    for clinic, count in sorted(
        summary["clinics"].items()
    ):
        print(
            f"{clinic:<35} "
            f"{count:>6}"
        )

    print("\n" + "=" * 60)


def dry_run_prediction_history():
    """
    Generate and report historical predictions without
    writing anything to the database.
    """

    records, summary = (
        build_prediction_history()
    )

    print_prediction_summary(
        summary
    )

    return records, summary


@transaction.atomic
def save_prediction_history(
    replace_existing=True,
):
    """
    Generate and save synthetic historical prediction data.

    PredictionData.timestamp uses auto_now_add=True.

    The current database backend does not return primary keys
    from bulk_create(), so records are retrieved after insertion
    and then backdated using QuerySet.update().
    """

    records, summary = build_prediction_history()

    if replace_existing:
        PredictionData.objects.all().delete()

    historical_timestamps = [
        record.timestamp
        for record in records
    ]

    # Allow auto_now_add to assign the initial timestamp.
    for record in records:
        record.timestamp = None

    # Remember the current highest ID.
    last_existing_id = (
        PredictionData.objects
        .order_by("-id")
        .values_list("id", flat=True)
        .first()
        or 0
    )

    PredictionData.objects.bulk_create(
        records,
        batch_size=500,
    )

    # MySQL does not populate PKs on the Python objects after
    # bulk_create(), so retrieve the newly inserted rows.
    created_records = list(
        PredictionData.objects
        .filter(id__gt=last_existing_id)
        .order_by("id")
    )

    if len(created_records) != len(historical_timestamps):
        raise RuntimeError(
            f"Expected {len(historical_timestamps)} "
            f"new predictions but found "
            f"{len(created_records)}."
        )

    # Backdate synthetic predictions.
    for record, historical_timestamp in zip(
        created_records,
        historical_timestamps,
    ):
        PredictionData.objects.filter(
            pk=record.pk
        ).update(
            timestamp=historical_timestamp
        )

    print_prediction_summary(summary)

    print(
        "\n✓ Prediction history saved successfully "
        "with historical timestamps."
    )

    return summary