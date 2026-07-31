from django.core.management.base import BaseCommand

from main_page.utils.demo_data.clinics import create_clinics
from main_page.utils.demo_data.users import create_users
from main_page.utils.demo_data.patients import create_patients


class Command(BaseCommand):
    help = "Generate IntelliCareAI Enterprise Demo"

    def handle(self, *args, **kwargs):

        self.stdout.write(
            self.style.SUCCESS("Starting IntelliCareAI Demo Generator\n")
        )

        # Create Clinics
        clinics = create_clinics()
        self.stdout.write(
            self.style.SUCCESS(f"✓ {len(clinics)} clinics ready.")
        )

        # Create Users
        create_users()
        self.stdout.write(
            self.style.SUCCESS("✓ Demo users ready.")
        )

        # Create Patients
        create_patients()
        self.stdout.write(
            self.style.SUCCESS("✓ Demo patients ready.")
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("🎉 IntelliCareAI Demo Environment Created Successfully!")
        )