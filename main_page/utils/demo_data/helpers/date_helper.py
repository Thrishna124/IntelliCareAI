import random
from datetime import timedelta

from django.utils import timezone


def generate_historical_dates(
    count,
    months_back=18,
):
    """
    Generate irregular historical dates for demo predictions.

    Dates are spread across the requested historical period
    and returned chronologically.
    """

    if count <= 0:
        return []

    now = timezone.now()
    max_days_back = months_back * 30

    dates = []

    for _ in range(count):

        days_back = random.randint(
            1,
            max_days_back,
        )

        historical_date = now - timedelta(
            days=days_back,
            hours=random.randint(0, 12),
            minutes=random.randint(0, 59),
        )

        dates.append(historical_date)

    return sorted(dates)


def generate_followup_date(
    previous_date,
    high_risk=False,
):
    """
    Generate a realistic follow-up date.

    High-risk patients are generally reassessed sooner.
    """

    if high_risk:

        days_until_followup = random.randint(
            14,
            60,
        )

    else:

        days_until_followup = random.randint(
            45,
            150,
        )

    followup_date = previous_date + timedelta(
        days=days_until_followup
    )

    now = timezone.now()

    if followup_date > now:
        return None

    return followup_date


def random_prediction_count(
    minimum=1,
    maximum=4,
):
    """
    Return a weighted prediction-history count.

    Most patients receive 2-3 assessments while fewer
    patients receive only one or several follow-ups.
    """

    choices = list(
        range(minimum, maximum + 1)
    )

    if choices == [1, 2, 3, 4]:

        weights = [
            0.15,  # 1 prediction
            0.35,  # 2 predictions
            0.35,  # 3 predictions
            0.15,  # 4 predictions
        ]

        return random.choices(
            choices,
            weights=weights,
            k=1,
        )[0]

    return random.randint(
        minimum,
        maximum,
    )