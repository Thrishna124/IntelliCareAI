from django.db import models


class GenderChoices(models.TextChoices):
    MALE = "Male", "Male"
    FEMALE = "Female", "Female"


class ActivityLevelChoices(models.TextChoices):
    SEDENTARY = "sedentary", "Sedentary (little or no exercise)"
    LIGHT = "light", "Lightly active (light exercise 1-3 days/week)"
    MODERATE = "moderate", "Moderately active (moderate exercise 3-5 days/week)"
    ACTIVE = "active", "Very active (hard exercise 6-7 days/week)"
    SUPER_ACTIVE = "super_active", "Super active (very hard exercise/physical job)"


class YesNoChoices(models.TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"


class NormalAbnormalChoices(models.TextChoices):
    NORMAL = "normal", "Normal"
    ABNORMAL = "abnormal", "Abnormal"


class PresentNotPresentChoices(models.TextChoices):
    PRESENT = "present", "Present"
    NOT_PRESENT = "notpresent", "Not Present"


class AppetiteChoices(models.TextChoices):
    GOOD = "good", "Good"
    POOR = "poor", "Poor"


class PredictionTypeChoices(models.TextChoices):
    PANCREAS = "pancreas", "Pancreas"
    HEART = "heart", "Heart"
    LIVER = "liver", "Liver"
    KIDNEY = "kidney", "Kidney"
    LUNGS = "lungs", "Lungs"
    FITNESS = "fitness", "Fitness"
    LUNG_CANCER = "lung_cancer", "Lung Cancer"