from main_page.models import Clinic
from .config import CLINICS


def create_clinics():
    clinics = []

    print("\nCreating Clinics...")

    for data in CLINICS:

        clinic, created = Clinic.objects.get_or_create(
            registration_number=data["registration_number"],
            defaults={
                "name": data["name"],
                "email": data["email"],
                "phone": data["phone"],
                "address": data["address"],
                "city": data["city"],
                "state": data["state"],
                "country": data["country"],
                "website": data["website"],
            },
        )

        if created:
            print(f"✓ Created {clinic.name}")
        else:
            print(f"• {clinic.name} already exists")

        clinics.append(clinic)

    return clinics