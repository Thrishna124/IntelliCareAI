
from django.contrib.auth.models import User

from main_page.models import UserProfile


def create_user(
    *,
    username,
    password,
    first_name,
    last_name,
    email,
    role,
    clinic=None,
    designation="",
    phone="",
):

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "is_staff": role in [
                "doctor",
                "clinic_admin",
                "system_admin",
                "receptionist",
            ],
            "is_superuser": role == "system_admin",
            "is_active": True,
        },
    )

    if created:
        user.set_password(password)

    # Always keep user information up to date
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.is_staff = role in [
        "doctor",
        "clinic_admin",
        "system_admin",
        "receptionist",
    ]
    user.is_superuser = role == "system_admin"
    user.is_active = True
    user.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Always update the profile
    profile.clinic = clinic
    profile.role = role
    profile.designation = designation

    # Only set phone if your UserProfile model has this field
    if hasattr(profile, "phone"):
        profile.phone = phone

    profile.save()

    return user