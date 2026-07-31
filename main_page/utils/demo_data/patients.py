from django.contrib.auth.models import User

from main_page.models import Clinic, PatientData

from .config import DEMO_CONFIG
from .helpers.faker_helper import (
    address,
    dob,
    first_name,
    last_name,
    middle_name,
    phone,
)
from .helpers.patient_helper import (
    random_age,
    random_gender,
    random_lifestyle,
)


def create_patients():

    print("\nCreating Patients...")

    total = 0

    # Start from the last existing patient ID
    last_patient = PatientData.objects.order_by("-pid").first()
    pid = (last_patient.pid + 1) if last_patient and last_patient.pid else 100001

    clinics = Clinic.objects.order_by("name")

    for clinic in clinics:

        print(f"\nGenerating patients for {clinic.name}")

        staff = User.objects.filter(
                profile__clinic=clinic,
                profile__role__in=["clinic_admin", "receptionist", "doctor"],
            ).first()
       

        if not staff:
            print(f"⚠ No staff found for {clinic.name}. Skipping...")
            continue

        for _ in range(DEMO_CONFIG["patients_per_clinic"]):

            gender = random_gender()
            age = random_age()
            fname = first_name(gender)
            lifestyle = random_lifestyle()

            addr = address()

            PatientData.objects.create(

                pid=pid,

                fname=fname,

                mname=middle_name(),

                lname=last_name(),

                age=age,

                DOB=dob(age),

                sex=gender,

                phone_cell=phone(),

                address=addr["address"],
                city=addr["city"],
                state=addr["state"],
                pincode=addr["pincode"],

                country_code="IN",

                lifestyle=lifestyle,

                clinic=clinic,

                user=staff,
            )

            pid += 1
            total += 1

        print(f"✓ {DEMO_CONFIG['patients_per_clinic']} patients created")

    print(f"\n🎉 Total Patients Created: {total}")