from datetime import timedelta
from multiprocessing import context

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from main_page.analytics import insights
from main_page.models import PatientData, PredictionData


class AnalyticsService:
    """
    Central service responsible for aggregating analytics data
    for the IntelliCareAI dashboard.
    """

    @staticmethod
    def patient_summary():
        """Patient overview statistics."""

        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        return {
            "total_patients": PatientData.objects.count(),

            "new_patients": PatientData.objects.filter(
                date__gte=last_30_days
            ).count(),

            "average_age": round(
                PatientData.objects.aggregate(
                    Avg("age")
                )["age__avg"] or 0,
                1,
            ),
        }

    @staticmethod
    def prediction_summary():
        """Prediction overview statistics."""

        total_predictions = PredictionData.objects.count()

        positive_predictions = PredictionData.objects.filter(
            prediction="Yes"
        ).count()

        negative_predictions = PredictionData.objects.filter(
            prediction="No"
        ).count()

        return {
            "total_predictions": total_predictions,
            "positive_predictions": positive_predictions,
            "negative_predictions": negative_predictions,
        }

    @staticmethod
    def module_distribution():
        """Predictions grouped by module."""

        return list(
            PredictionData.objects
            .values("prediction_type")
            .annotate(total=Count("id"))
            .order_by("prediction_type")
        )

    @staticmethod
    def disease_distribution():
        """Yes / No prediction distribution."""

        return list(
            PredictionData.objects
            .values("prediction")
            .annotate(total=Count("id"))
        )

    @staticmethod
    def demographics():
        """Gender distribution."""

        return list(
            PatientData.objects
            .values("sex")
            .annotate(total=Count("id"))
        )

    @staticmethod
    def prediction_trend():
        """Daily prediction counts."""

        return list(
            PredictionData.objects
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )

    @staticmethod
    def dashboard_context():
        """Return the complete analytics context."""

        context = {}

        context.update(AnalyticsService.patient_summary())
        context.update(AnalyticsService.prediction_summary())

        context["module_distribution"] = AnalyticsService.module_distribution()
        context["disease_distribution"] = AnalyticsService.disease_distribution()
        context["gender_distribution"] = AnalyticsService.demographics()
        context["prediction_trend"] = AnalyticsService.prediction_trend()

        return context
    
    @staticmethod
    def age_distribution():
        """
        Patient distribution by age group.
        """

        groups = {
            "0-18": 0,
            "19-35": 0,
            "36-50": 0,
            "51-65": 0,
            "65+": 0,
        }

        for patient in PatientData.objects.only("age"):

            age = patient.age or 0

            if age <= 18:
                groups["0-18"] += 1

            elif age <= 35:
                groups["19-35"] += 1

            elif age <= 50:
                groups["36-50"] += 1

            elif age <= 65:
                groups["51-65"] += 1

            else:
                groups["65+"] += 1

        return [
        {
            "group": key,
            "total": value,
        }
        for key, value in groups.items()
    ]

    @staticmethod
    def lifestyle_distribution():
        """
        Distribution of patient lifestyles.
        """

        return list(
            PatientData.objects
            .values("lifestyle")
            .annotate(total=Count("id"))
            .order_by("lifestyle")
    )
    @staticmethod
    def ai_insights():  
        """
        Generate dashboard insights.
        """

        insights = []

        total_patients = PatientData.objects.count()

        total_predictions = PredictionData.objects.count()

        positives = PredictionData.objects.filter(
            prediction="Yes"
        ).count()

        if total_patients:
            insights.append(
            f"{total_patients} patients are registered in IntelliCareAI."
        )

        if total_predictions:
            insights.append(
            f"{total_predictions} AI predictions have been generated."
        )

        if positives:
            insights.append(
            f"{positives} predictions indicate a positive diagnosis."
        )

        most_used = (
            PredictionData.objects
            .values("prediction_type")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
         )

        if most_used:
            insights.append(
            f"{most_used['prediction_type']} is the most frequently used prediction module."
        )

        return insights

    @staticmethod
    def export_report():
        """Return a privacy-conscious, aggregated analytics report for CSV export."""

        context = AnalyticsService.dashboard_context()
        rows = [
            ("Population health", "Total patients", context["total_patients"]),
            ("Population health", "New patients (30 days)", context["new_patients"]),
            ("Population health", "Average age", context["average_age"]),
            ("Predictions", "Total predictions", context["total_predictions"]),
            ("Predictions", "Positive cases", context["positive_predictions"]),
            ("Predictions", "Negative cases", context["negative_predictions"]),
        ]

        for item in context["module_distribution"]:
            rows.append(("Prediction module", item["prediction_type"] or "Unspecified", item["total"]))

        for item in context["disease_distribution"]:
            rows.append(("Prediction outcome", item["prediction"] or "Unspecified", item["total"]))

        for insight in context["ai_insights"]:
            rows.append(("AI insight", "Executive intelligence", insight))

        return rows
    
    ########## Contextual Insights ##########

    @staticmethod
    def dashboard_context():
        """Return the complete analytics context."""

        context = {}

        context.update(AnalyticsService.patient_summary())
        context.update(AnalyticsService.prediction_summary())

        context["module_distribution"] = AnalyticsService.module_distribution()
        context["disease_distribution"] = AnalyticsService.disease_distribution()
        context["gender_distribution"] = AnalyticsService.demographics()
        context["prediction_trend"] = AnalyticsService.prediction_trend()

    # New analytics
        context["age_distribution"] = AnalyticsService.age_distribution()
        context["lifestyle_distribution"] = AnalyticsService.lifestyle_distribution()
        context["ai_insights"] = AnalyticsService.ai_insights()

        return context
