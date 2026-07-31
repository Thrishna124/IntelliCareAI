"""
IntelliCareAI Enterprise Demo Configuration
"""

# ==========================================================
# GENERAL SETTINGS
# ==========================================================

DEMO_CONFIG = {
    "number_of_clinics": 2,
    "clinic_admins_per_clinic": 1,
    "doctors_per_clinic": 3,
    "receptionists_per_clinic": 1,
    "patients_per_clinic": 100,
    "patient_portal_users": 20,
    "prediction_history_months": 18,
    "random_seed": 42,
    "default_password": "Password@123",
}


PATIENT_CONFIG = {
    "min_age": 18,
    "max_age": 90,

    "male_percentage": 50,
    "female_percentage": 50,
}

# ==========================================================
# CLINICS
# ==========================================================

CLINICS = [
    {
        "registration_number": "KER-SMC-0001",
        "name": "Sunrise Medical Center",
        "email": "info@sunrisemedical.demo",
        "phone": "+91-484-555-1001",
        "address": "MG Road",
        "city": "Kochi",
        "state": "Kerala",
        "country": "India",
        "website": "https://sunrisemedical.demo",
        "clinic_type": "hospital",
        "established_year": 1998,
        "license_expiry": "2030-12-31",
    },
    {
        "registration_number": "KER-CCH-0001",
        "name": "CityCare Hospital",
        "email": "info@citycare.demo",
        "phone": "+91-495-555-1001",
        "address": "Medical College Road",
        "city": "Calicut",
        "state": "Kerala",
        "country": "India",
        "website": "https://citycare.demo",
        "clinic_type": "hospital",
        "established_year": 2005,
        "license_expiry": "2031-06-30",
    },
]


# ==========================================================
# DEMO USERS
# ==========================================================

DEMO_USERS = {

    # -----------------------------
    # System Administrator
    # -----------------------------

    "system_admin": {
        "username": "admin",
        "password": DEMO_CONFIG["default_password"],
        "first_name": "System",
        "last_name": "Administrator",
        "email": "admin@intellicare.demo",
        "designation": "Platform Administrator",
        "role": "system_admin",
    },

    # -----------------------------
    # Clinic Staff
    # -----------------------------

    "clinics": [

        {
            "registration_number": "KER-SMC-0001",

            "admin": {
                "username": "sunrise_admin",
                "password": DEMO_CONFIG["default_password"],
                "first_name": "Anita",
                "last_name": "Menon",
                "email": "admin@sunrisemedical.demo",
                "designation": "Clinic Administrator",
                "role": "clinic_admin",
            },

            "doctors": [

                {
                    "username": "sunrise_doc1",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Arjun",
                    "last_name": "Nair",
                    "email": "arjun@sunrisemedical.demo",
                    "designation": "Cardiologist",
                    "role": "doctor",
                },

                {
                    "username": "sunrise_doc2",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Meera",
                    "last_name": "Joseph",
                    "email": "meera@sunrisemedical.demo",
                    "designation": "General Physician",
                    "role": "doctor",
                },

                {
                    "username": "sunrise_doc3",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Rahul",
                    "last_name": "Pillai",
                    "email": "rahul@sunrisemedical.demo",
                    "designation": "Nephrologist",
                    "role": "doctor",
                },

            ],

            "receptionists": [

                {
                    "username": "sunrise_reception",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Neha",
                    "last_name": "Das",
                    "email": "frontdesk@sunrisemedical.demo",
                    "designation": "Receptionist",
                    "role": "receptionist",
                }

            ],
        },

        {
            "registration_number": "KER-CCH-0001",

            "admin": {
                "username": "citycare_admin",
                "password": DEMO_CONFIG["default_password"],
                "first_name": "Suresh",
                "last_name": "Kumar",
                "email": "admin@citycare.demo",
                "designation": "Clinic Administrator",
                "role": "clinic_admin",
            },

            "doctors": [

                {
                    "username": "citycare_doc1",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Vivek",
                    "last_name": "Menon",
                    "email": "vivek@citycare.demo",
                    "designation": "Pulmonologist",
                    "role": "doctor",
                },

                {
                    "username": "citycare_doc2",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Anjali",
                    "last_name": "Thomas",
                    "email": "anjali@citycare.demo",
                    "designation": "Endocrinologist",
                    "role": "doctor",
                },

                {
                    "username": "citycare_doc3",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Akhil",
                    "last_name": "Nair",
                    "email": "akhil@citycare.demo",
                    "designation": "Hepatologist",
                    "role": "doctor",
                },

            ],

            "receptionists": [

                {
                    "username": "citycare_reception",
                    "password": DEMO_CONFIG["default_password"],
                    "first_name": "Sneha",
                    "last_name": "Roy",
                    "email": "frontdesk@citycare.demo",
                    "designation": "Receptionist",
                    "role": "receptionist",
                }

            ],

            "PATIENT_CONFIG ": {
            "min_age": 18,
            "max_age": 90,
            "male_percentage": 52,
            "female_percentage": 48,
            "blood_groups": [
             "A+","A-",
            "B+","B-",
            "AB+","AB-",
            "O+","O-"
    ]
}
        },

    ],
}

