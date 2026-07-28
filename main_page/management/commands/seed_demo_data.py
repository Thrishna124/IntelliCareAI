"""Create synthetic, repeatable demo data for IntelliCareAI."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from main_page.models import DQScore, FormVitals, PatientData, PredictionData


DEMO_PASSWORD = "DemoPass123!"

CLINICIANS = (
    ("demo.admin", "Asha", "Rao", "Administrator"),
    ("demo.clinician", "Vikram", "Mehta", "Clinician"),
    ("demo.analyst", "Nisha", "Iyer", "Clinical Analyst"),
)

PATIENTS = (
    (900001, "Anita", "Sharma", 29, "Female", "active"),
    (900002, "Rahul", "Nair", 42, "Male", "moderate"),
    (900003, "Meera", "Das", 58, "Female", "light"),
    (900004, "Arjun", "Kapoor", 66, "Male", "sedentary"),
    (900005, "Kavya", "Menon", 35, "Female", "active"),
    (900006, "Sanjay", "Patel", 51, "Male", "moderate"),
    (900007, "Priya", "Reddy", 47, "Female", "light"),
    (900008, "Dev", "Singh", 61, "Male", "sedentary"),
    (900009, "Isha", "Verma", 38, "Female", "active"),
    (900010, "Rohan", "Gupta", 55, "Male", "moderate"),
    (900011, "Leela", "Bose", 44, "Female", "light"),
    (900012, "Kiran", "Joshi", 70, "Male", "sedentary"),
)

PREDICTIONS = (
    ("heart", "No", "No significant cardiac risk pattern identified."),
    ("pancreas", "Yes", "Elevated diabetes risk detected."),
    ("kidney", "No", "Kidney function indicators within the expected range."),
    ("liver", "No", "No liver disorder pattern identified."),
    ("lungs", "Yes", "Respiratory function requires clinical follow-up."),
    ("fitness", "No", "Lifestyle plan generated for preventive care."),
)


class Command(BaseCommand):
    help = "Create synthetic clinicians, patients, vitals, and prediction history for a demo environment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reset passwords for the named demo clinicians.",
        )

    def handle(self, *args, **options):
        clinicians = self._create_clinicians(reset_passwords=options["reset_passwords"])
        patient_count, prediction_count = self._create_patients_and_history(clinicians)

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {len(clinicians)} clinicians, {patient_count} patients, "
            f"{prediction_count} predictions."
        ))
        self.stdout.write("Demo login: demo.clinician / DemoPass123!")
        self.stdout.write("All records are synthetic and use patient IDs 900001–900012.")

    def _create_clinicians(self, reset_passwords):
        clinicians = []
        for username, first_name, last_name, title in CLINICIANS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@example.test",
                    "is_staff": username == "demo.admin",
                },
            )
            if created or reset_passwords:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
            clinicians.append(user)
            self.stdout.write(f"{'Created' if created else 'Kept'} {title}: {username}")
        return clinicians

    def _create_patients_and_history(self, clinicians):
        now = timezone.now()
        patient_count = 0
        prediction_count = 0

        for index, (pid, first_name, last_name, age, sex, lifestyle) in enumerate(PATIENTS):
            clinician = clinicians[index % len(clinicians)]
            patient, created = PatientData.objects.update_or_create(
                pid=pid,
                defaults={
                    "user": clinician,
                    "fname": first_name,
                    "lname": last_name,
                    "age": age,
                    "DOB": (now - timedelta(days=age * 365 + 120)).date(),
                    "sex": sex,
                    "phone_cell": f"90000{index:05d}"[-10:],
                    "address": "Synthetic demonstration record",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "country_code": "IN",
                    "pincode": "560001",
                    "lifestyle": lifestyle,
                },
            )
            patient_count += int(created)

            FormVitals.objects.update_or_create(
                pid=patient,
                defaults={
                    "height": 155 + (index % 5) * 5,
                    "weight": 55 + (index % 6) * 6,
                    "heart_rate": 68 + (index % 9),
                    "temperature": 36.6,
                    "respiration_rate": 15 + (index % 4),
                    "BMI": 23.1,
                    "BMI_status": "Healthy Weight",
                },
            )

            for prediction_index, (module, outcome, diagnosis) in enumerate(PREDICTIONS):
                recorded_at = now - timedelta(days=index * 3 + prediction_index * 2)
                prediction, prediction_created = PredictionData.objects.update_or_create(
                    pid=patient,
                    prediction_type=module,
                    diagnosis=diagnosis,
                    defaults={"prediction": outcome, "image": ""},
                )
                PredictionData.objects.filter(pk=prediction.pk).update(timestamp=recorded_at)

                dq_score, _ = DQScore.objects.update_or_create(
                    pid=patient,
                    prediction_type=module,
                    defaults={
                        "total_features_count": 12,
                        "missing_features_count": prediction_index % 3,
                        "data_quality_value": 0.92 - prediction_index * 0.03,
                    },
                )
                DQScore.objects.filter(pk=dq_score.pk).update(timestamp=recorded_at)
                prediction_count += int(prediction_created)

        return patient_count, prediction_count
