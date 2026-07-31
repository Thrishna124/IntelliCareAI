import random

from ..config import PATIENT_CONFIG


def random_gender():

    return random.choices(
        ["Male", "Female"],
        weights=[
            PATIENT_CONFIG["male_percentage"],
            PATIENT_CONFIG["female_percentage"],
        ],
    )[0]


def random_age():

    return random.randint(
        PATIENT_CONFIG["min_age"],
        PATIENT_CONFIG["max_age"],
    )


def random_lifestyle():

    return random.choice([
        "sedentary",
        "light",
        "moderate",
        "active",
        "super_active",
    ])