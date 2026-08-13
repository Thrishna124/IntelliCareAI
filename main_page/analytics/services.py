from datetime import timedelta

from django.db.models import Avg
from django.utils import timezone

from main_page.analytics import insights, queries
from main_page.models import PatientData


class AnalyticsService:
    """
    Enterprise Analytics Service.

    This service coordinates the analytics layer and exposes
    a clean API to views.py.

    All database-heavy analytics queries are delegated to
    analytics/queries.py.
    """

    @staticmethod
    def patient_summary(clinic=None):
        """
        Basic patient statistics.
        """

        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        patients = PatientData.objects.filter(
            clinic__isnull=False
        )

        if clinic is not None:
            patients = patients.filter(
                clinic=clinic
            )

        return {
            "total_patients": patients.count(),

            "new_patients": patients.filter(
                date__gte=last_30_days
            ).count(),

            "average_age": round(
                patients.aggregate(
                    Avg("age")
                )["age__avg"] or 0,
                1,
            ),
        }

    @staticmethod
    def dashboard_context(clinic=None):
        """
        Complete Enterprise Analytics dashboard context.
        """

        context = {}

        # --------------------------------------------
        # Patient Summary
        # --------------------------------------------

        context.update(
            AnalyticsService.patient_summary(clinic)
        )

        # --------------------------------------------
        # KPI Summary
        # --------------------------------------------

        context.update(
            queries.get_kpi_summary(clinic)
        )

        # --------------------------------------------
        # Charts
        # --------------------------------------------

        context["prediction_trend"] = (
            queries.get_monthly_prediction_trend(clinic)
        )

        context["positive_prediction_trend"] = (
            queries.get_monthly_positive_trend(clinic)
        )

        context["disease_distribution"] = (
            queries.get_disease_distribution(clinic)
        )

        context["module_distribution"] = (
            queries.get_prediction_volume_by_type(clinic)
        )

        context["gender_distribution"] = (
            queries.get_gender_distribution(clinic)
        )

        context["age_distribution"] = (
            queries.get_age_distribution(clinic)
        )

        context["lifestyle_distribution"] = (
            queries.get_lifestyle_distribution(clinic)
        )

        # --------------------------------------------
        # Enterprise Analytics
        # --------------------------------------------

        context["clinic_comparison"] = (
            queries.get_clinic_comparison()
        )

        context["high_risk_patient_list"] = (
            queries.get_high_risk_patients(clinic)
        )

        # --------------------------------------------
        # AI Insights
        # --------------------------------------------

        context["ai_insights"] = (
            insights.generate(context)
            if hasattr(insights, "generate")
            else []
        )

        return context

    @staticmethod
    def export_report():
        """
        Privacy-safe analytics export.
        """

        context = AnalyticsService.dashboard_context()

        rows = [

            ("Population Health", "Total Patients",
             context["total_patients"]),

            ("Population Health", "New Patients (30 Days)",
             context["new_patients"]),

            ("Population Health", "Average Age",
             context["average_age"]),

            ("Predictions", "Total Predictions",
             context["total_predictions"]),

            ("Predictions", "Positive Predictions",
             context["positive_predictions"]),

            ("Predictions", "Negative Predictions",
             context["negative_predictions"]),

            ("Predictions", "Positive Rate (%)",
             context["positive_rate"]),
        ]

        # --------------------------------------------
        # Prediction Modules
        # --------------------------------------------

        for item in context["module_distribution"]:

            rows.append(

                (
                    "Prediction Module",
                    item["label"],
                    item["count"],
                )

            )

        # --------------------------------------------
        # Disease Distribution
        # --------------------------------------------

        for item in context["disease_distribution"]:

            rows.append(

                (
                    "Disease Distribution",
                    item["label"],
                    item["count"],
                )

            )

        # --------------------------------------------
        # Clinic Comparison
        # --------------------------------------------

        for clinic in context["clinic_comparison"]:

            rows.append(

                (
                    "Clinic",
                    clinic["clinic"],
                    clinic["positive_rate"],
                )

            )

        # --------------------------------------------
        # AI Insights
        # --------------------------------------------

        #for insight in context["ai_insights"]:

        #    rows.append(

        #        (
        #            "AI Insight",
        #            "Executive Intelligence",
        #            insight,
        #        )

        #    )

        #return rows

        context["ai_insights"] = []