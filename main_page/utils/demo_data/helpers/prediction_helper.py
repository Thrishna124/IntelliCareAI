import random


# ==========================================================
# LIFESTYLE / ACTIVITY MAPPING
# ==========================================================

ACTIVITY_SCORES = {
    "sedentary": 0,
    "light": 1,
    "moderate": 2,
    "active": 3,
    "super_active": 4,
}


def clamp(value, minimum=0.0, maximum=1.0):
    """
    Keep a numeric value inside a specified range.
    """
    return max(minimum, min(value, maximum))


# ==========================================================
# PATIENT HEALTH PROFILE
# ==========================================================

def build_patient_health_profile(patient):
    """
    Build a persistent synthetic health profile for a patient.

    The profile is derived from existing PatientData fields
    such as age, sex and lifestyle, while adding realistic
    synthetic characteristics required for analytics.

    This does NOT modify PatientData.
    """

    age = patient.age or 40

    lifestyle = (
        patient.lifestyle or "moderate"
    ).lower()

    activity_score = ACTIVITY_SCORES.get(
        lifestyle,
        2,
    )

    # ------------------------------------------------------
    # BMI
    # ------------------------------------------------------

    bmi_mean = 27.0

    if activity_score == 0:
        bmi_mean += 3.0

    elif activity_score == 1:
        bmi_mean += 1.5

    elif activity_score == 3:
        bmi_mean -= 1.5

    elif activity_score == 4:
        bmi_mean -= 2.5

    if age >= 50:
        bmi_mean += 0.8

    bmi = random.gauss(
        bmi_mean,
        3.5,
    )

    bmi = round(
        max(17.5, min(bmi, 42.0)),
        1,
    )

    # ------------------------------------------------------
    # SMOKING
    # ------------------------------------------------------

    smoking_probability = 0.14

    if activity_score == 0:
        smoking_probability += 0.08

    if age >= 45:
        smoking_probability += 0.04

    smoker = (
        random.random()
        < smoking_probability
    )

    # Some smokers have substantially heavier exposure.
    if smoker:

        smoking_intensity = random.choices(
            ["light", "moderate", "heavy"],
            weights=[0.40, 0.40, 0.20],
            k=1,
        )[0]

    else:
        smoking_intensity = "none"

    # ------------------------------------------------------
    # ALCOHOL
    # ------------------------------------------------------

    alcohol_level = random.choices(
        [
            "none",
            "occasional",
            "moderate",
            "high",
        ],
        weights=[
            0.35,
            0.38,
            0.20,
            0.07,
        ],
        k=1,
    )[0]

    # ------------------------------------------------------
    # HYPERTENSION
    # ------------------------------------------------------

    hypertension_probability = 0.08

    if age >= 40:
        hypertension_probability += 0.08

    if age >= 55:
        hypertension_probability += 0.15

    if age >= 70:
        hypertension_probability += 0.12

    if bmi >= 30:
        hypertension_probability += 0.12

    if smoker:
        hypertension_probability += 0.05

    if activity_score == 0:
        hypertension_probability += 0.06

    hypertension = (
        random.random()
        < clamp(hypertension_probability)
    )

    # ------------------------------------------------------
    # DIABETES TENDENCY
    # ------------------------------------------------------

    diabetes_probability = 0.05

    if age >= 45:
        diabetes_probability += 0.08

    if age >= 60:
        diabetes_probability += 0.08

    if bmi >= 25:
        diabetes_probability += 0.05

    if bmi >= 30:
        diabetes_probability += 0.12

    if activity_score == 0:
        diabetes_probability += 0.08

    diabetes_tendency = (
        random.random()
        < clamp(diabetes_probability)
    )

    # ------------------------------------------------------
    # BASE CARDIOVASCULAR RISK
    # ------------------------------------------------------

    cardiovascular_risk = 0.04

    cardiovascular_risk += (
        max(age - 35, 0) * 0.006
    )

    if bmi >= 30:
        cardiovascular_risk += 0.10

    if smoker:
        cardiovascular_risk += 0.15

    if hypertension:
        cardiovascular_risk += 0.18

    if diabetes_tendency:
        cardiovascular_risk += 0.10

    cardiovascular_risk -= (
        activity_score * 0.025
    )

    cardiovascular_risk = clamp(
        cardiovascular_risk,
        0.02,
        0.90,
    )

    # ------------------------------------------------------
    # RETURN PROFILE
    # ------------------------------------------------------

    return {
        "age": age,
        "sex": patient.sex,
        "lifestyle": lifestyle,
        "activity_score": activity_score,

        "bmi": bmi,

        "smoker": smoker,
        "smoking_intensity": smoking_intensity,

        "alcohol_level": alcohol_level,

        "hypertension": hypertension,
        "diabetes_tendency": diabetes_tendency,

        "cardiovascular_risk": round(
            cardiovascular_risk,
            3,
        ),
    }

# ==========================================================
# DISEASE-SPECIFIC RISK ENGINE
# ==========================================================

def calculate_disease_risks(profile):
    """
    Calculate correlated disease-specific risk scores from
    the persistent patient health profile.

    Scores represent synthetic probabilities between
    0.01 and 0.95.

    Small random variation prevents the demo population from
    looking mathematically deterministic.
    """

    age = profile["age"]
    bmi = profile["bmi"]

    activity = profile["activity_score"]

    smoker = profile["smoker"]
    smoking_intensity = profile["smoking_intensity"]

    alcohol = profile["alcohol_level"]

    hypertension = profile["hypertension"]
    diabetes = profile["diabetes_tendency"]

    cardio = profile["cardiovascular_risk"]

    # ------------------------------------------------------
    # HEART DISEASE
    # ------------------------------------------------------

    heart = cardio

    if age >= 65:
        heart += 0.05

    if smoking_intensity == "heavy":
        heart += 0.08

    heart += random.uniform(
        -0.05,
        0.05,
    )

    # ------------------------------------------------------
    # KIDNEY DISEASE
    # ------------------------------------------------------

    kidney = 0.04

    kidney += max(
        age - 45,
        0,
    ) * 0.004

    if hypertension:
        kidney += 0.20

    if diabetes:
        kidney += 0.18

    if bmi >= 30:
        kidney += 0.06

    kidney += random.uniform(
        -0.04,
        0.05,
    )

    # ------------------------------------------------------
    # LIVER DISEASE
    # ------------------------------------------------------

    liver = 0.035

    if bmi >= 25:
        liver += 0.06

    if bmi >= 30:
        liver += 0.10

    if diabetes:
        liver += 0.08

    alcohol_risk = {
        "none": 0.00,
        "occasional": 0.02,
        "moderate": 0.10,
        "high": 0.28,
    }

    liver += alcohol_risk.get(
        alcohol,
        0,
    )

    liver += random.uniform(
        -0.03,
        0.05,
    )

    # ------------------------------------------------------
    # LUNG DISEASE
    # ------------------------------------------------------

    lungs = 0.025

    smoking_risk = {
        "none": 0.00,
        "light": 0.12,
        "moderate": 0.25,
        "heavy": 0.42,
    }

    lungs += smoking_risk.get(
        smoking_intensity,
        0,
    )

    if age >= 60:
        lungs += 0.08

    if age >= 75:
        lungs += 0.06

    lungs += random.uniform(
        -0.03,
        0.05,
    )

    # ------------------------------------------------------
    # LUNG CANCER
    # ------------------------------------------------------

    lung_cancer = 0.01

    lung_cancer_smoking_risk = {
        "none": 0.00,
        "light": 0.05,
        "moderate": 0.13,
        "heavy": 0.28,
    }

    lung_cancer += (
        lung_cancer_smoking_risk.get(
            smoking_intensity,
            0,
        )
    )

    if smoker and age >= 55:
        lung_cancer += 0.08

    if smoker and age >= 70:
        lung_cancer += 0.07

    lung_cancer += random.uniform(
        -0.015,
        0.025,
    )

    # ------------------------------------------------------
    # DIABETES
    # ------------------------------------------------------

    pancreas = 0.04

    if age >= 45:
        pancreas += 0.06

    if age >= 60:
        pancreas += 0.05

    if bmi >= 25:
        pancreas += 0.07

    if bmi >= 30:
        pancreas += 0.15

    if diabetes:
        pancreas += 0.25

    if activity == 0:
        pancreas += 0.08

    elif activity >= 3:
        pancreas -= 0.04

    pancreas += random.uniform(
        -0.04,
        0.05,
    )

    # ------------------------------------------------------
    # POOR FITNESS RISK
    # ------------------------------------------------------

    fitness = 0.10

    fitness += {
        0: 0.45,
        1: 0.30,
        2: 0.17,
        3: 0.07,
        4: 0.02,
    }.get(
        activity,
        0.17,
    )

    if bmi >= 30:
        fitness += 0.12

    if smoker:
        fitness += 0.08

    if age >= 65:
        fitness += 0.05

    fitness += random.uniform(
        -0.05,
        0.05,
    )

    # ------------------------------------------------------
    # CLAMP SCORES
    # ------------------------------------------------------

    return {
        "heart": round(
            clamp(heart, 0.01, 0.95),
            3,
        ),

        "kidney": round(
            clamp(kidney, 0.01, 0.90),
            3,
        ),

        "liver": round(
            clamp(liver, 0.01, 0.85),
            3,
        ),

        "lungs": round(
            clamp(lungs, 0.01, 0.90),
            3,
        ),

        "lung_cancer": round(
            clamp(lung_cancer, 0.005, 0.70),
            3,
        ),

        "pancreas": round(
            clamp(pancreas, 0.01, 0.90),
            3,
        ),

        "fitness": round(
            clamp(fitness, 0.01, 0.90),
            3,
        ),
    }

# ==========================================================
# PREDICTION OUTCOME ENGINE
# ==========================================================

PREDICTION_THRESHOLDS = {
    "heart": 0.50,
    "kidney": 0.45,
    "liver": 0.40,
    "lungs": 0.40,
    "lung_cancer": 0.32,
    "pancreas": 0.45,
    "fitness": 0.55,
}


DIAGNOSIS_TEXT = {

    "heart": {
        "Yes": (
            "Elevated cardiac risk pattern detected. "
            "Clinical follow-up is recommended."
        ),
        "No": (
            "No significant cardiac risk pattern identified."
        ),
    },

    "kidney": {
        "Yes": (
            "Elevated kidney disease risk indicators detected. "
            "Renal function follow-up is recommended."
        ),
        "No": (
            "Kidney function indicators within the expected range."
        ),
    },

    "liver": {
        "Yes": (
            "Liver health indicators suggest elevated risk. "
            "Clinical evaluation is recommended."
        ),
        "No": (
            "No liver disorder pattern identified."
        ),
    },

    "lungs": {
        "Yes": (
            "Respiratory function requires clinical follow-up."
        ),
        "No": (
            "Respiratory indicators are within the expected range."
        ),
    },

    "lung_cancer": {
        "Yes": (
            "Elevated lung cancer risk pattern detected. "
            "Further clinical screening is recommended."
        ),
        "No": (
            "No significant lung cancer risk pattern identified."
        ),
    },

    "pancreas": {
        "Yes": (
            "Elevated diabetes risk detected."
        ),
        "No": (
            "No significant diabetes risk pattern identified."
        ),
    },

    "fitness": {
        "Yes": (
            "Reduced fitness indicators identified. "
            "Lifestyle improvement plan recommended."
        ),
        "No": (
            "Lifestyle plan generated for preventive care."
        ),
    },
}


def generate_prediction_outcome(
    prediction_type,
    risk_score,
):
    """
    Convert a synthetic risk score into the same Yes/No
    convention used by IntelliCareAI PredictionData.

    A small uncertainty zone around the threshold prevents
    perfectly deterministic demo outcomes.
    """

    threshold = PREDICTION_THRESHOLDS[
        prediction_type
    ]

    adjusted_score = (
        risk_score
        + random.uniform(-0.04, 0.04)
    )

    prediction = (
        "Yes"
        if adjusted_score >= threshold
        else "No"
    )

    diagnosis = DIAGNOSIS_TEXT[
        prediction_type
    ][prediction]

    return {
        "prediction": prediction,
        "diagnosis": diagnosis,
        "risk_score": risk_score,
    }