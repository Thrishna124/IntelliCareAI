from django.urls import reverse


def get_dashboard_redirect(user):
    """
    Return the correct dashboard URL based on the user's role.
    """

    role = user.profile.role

    if role == "individual":
        return reverse("individual:dashboard")

    elif role in ["doctor", "clinic_admin"]:
        return reverse("main_page:home")

    elif role == "system_admin":
        return reverse("admin_dashboard:home")

    return reverse("main_page:home")