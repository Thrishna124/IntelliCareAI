"""
Analytics chart utilities for the DocSpot main page.
"""

from typing import Any, Dict


def get_chart_ids() -> Dict[str, str]:
    return {
        "prediction_trend": "predictionTrendChart",
        "disease_distribution": "diseaseDistributionChart",
        "module_distribution": "moduleDistributionChart",
        "age_distribution": "ageDistributionChart",
        "gender_distribution": "genderDistributionChart",
        "lifestyle_distribution": "lifestyleDistributionChart",
    }