import random
from datetime import timedelta

from django.utils import timezone


def random_historical_date(
    months_back=10,
    minimum_days_ago=1,
):
    """
    Return a timezone-aware datetime randomly distributed
    across the historical demo period.

    Dates are intentionally irregular so analytics charts
    do not look artificially generated.
    """

    now = timezone.now()

    maximum_days_ago = months_back * 30

    days_ago = random.randint(
        minimum_days_ago,
        maximum_days_ago,
    )

    hour = random.randint(8, 18)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    historical_date = now - timedelta(days=days_ago)

    return historical_date.replace(
        hour=hour,
        minute=minute,
        second=second,
        microsecond=0,
    )


def generate_patient_timeline(
    count,
    months_back=10,
):
    """
    Generate an ordered historical prediction timeline
    for a single patient.

    Example:

        2025-11-14
        2026-01-03
        2026-03-27
        2026-06-08

    instead of evenly spaced artificial dates.
    """

    dates = [
        random_historical_date(months_back=months_back)
        for _ in range(count)
    ]

    return sorted(dates)


def generate_followup_date(
    previous_date,
    minimum_days=14,
    maximum_days=75,
):
    """
    Generate a realistic follow-up date after a previous
    prediction.

    Useful for patients with elevated risk who are more
    likely to receive another assessment.
    """

    followup_gap = random.randint(
        minimum_days,
        maximum_days,
    )

    followup = previous_date + timedelta(days=followup_gap)

    now = timezone.now()

    if followup > now:
        followup = now - timedelta(
            days=random.randint(1, 7)
        )

    return followup