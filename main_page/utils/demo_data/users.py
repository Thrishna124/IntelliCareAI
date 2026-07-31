from main_page.models import Clinic
from .config import DEMO_USERS
from .helpers.user_helper import create_user


def create_users():
    """
    Create all demo users for IntelliCareAI.
    Safe to run multiple times.
    """

    print("\nCreating Demo Users...")

    created_users = []

    # =====================================================
    # SYSTEM ADMIN
    # =====================================================

    admin = DEMO_USERS["system_admin"]

    create_user(
        username=admin["username"],
        password=admin["password"],
        first_name=admin["first_name"],
        last_name=admin["last_name"],
        email=admin["email"],
        role=admin["role"],
        designation=admin["designation"],
    )

    created_users.append(admin["username"])

    # =====================================================
    # CLINIC STAFF
    # =====================================================

    for clinic_info in DEMO_USERS["clinics"]:

        clinic = Clinic.objects.get(
            registration_number=clinic_info["registration_number"]
        )

        # -----------------------------
        # Clinic Admin
        # -----------------------------

        admin = clinic_info["admin"]

        create_user(
            username=admin["username"],
            password=admin["password"],
            first_name=admin["first_name"],
            last_name=admin["last_name"],
            email=admin["email"],
            role=admin["role"],
            clinic=clinic,
            designation=admin["designation"],
        )

        created_users.append(admin["username"])

        # -----------------------------
        # Doctors
        # -----------------------------

        for doctor in clinic_info["doctors"]:

            create_user(
                username=doctor["username"],
                password=doctor["password"],
                first_name=doctor["first_name"],
                last_name=doctor["last_name"],
                email=doctor["email"],
                role=doctor["role"],
                clinic=clinic,
                designation=doctor["designation"],
            )

            created_users.append(doctor["username"])

        # -----------------------------
        # Receptionists
        # -----------------------------

        for receptionist in clinic_info["receptionists"]:

            create_user(
                username=receptionist["username"],
                password=receptionist["password"],
                first_name=receptionist["first_name"],
                last_name=receptionist["last_name"],
                email=receptionist["email"],
                role=receptionist["role"],
                clinic=clinic,
                designation=receptionist["designation"],
            )

            created_users.append(receptionist["username"])

    print(f"✓ Created {len(created_users)} demo users")

    return created_users