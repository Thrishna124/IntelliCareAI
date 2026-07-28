from django.contrib import admin

from .models import Clinic, UserProfile


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "registration_number",
        "city",
        "state",
        "country",
        "is_active",
    )

    list_filter = (
        "is_active",
        "state",
        "country",
    )

    search_fields = (
        "name",
        "registration_number",
        "email",
        "city",
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "clinic",
        "designation",
        "phone",
    )

    list_filter = (
        "role",
        "clinic",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone",
    )