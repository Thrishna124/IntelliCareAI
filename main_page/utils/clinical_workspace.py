"""Helpers for the clinician-owned patient workspace."""

from main_page.models import PatientData


ACTIVE_PATIENT_SESSION_KEY = "active_patient_id"


def get_active_patient(request):
    """Return the patient selected by the signed-in clinician."""
    patient_id = request.session.get(ACTIVE_PATIENT_SESSION_KEY)
    if not patient_id or not request.user.is_authenticated:
        return None
    return PatientData.objects.filter(id=patient_id, user=request.user).first()


def set_active_patient(request, patient):
    """Store a clinician-owned patient selection in the session."""
    request.session[ACTIVE_PATIENT_SESSION_KEY] = patient.id

def clear_active_patient(request):
    """Remove the active patient from the session."""
    request.session.pop(ACTIVE_PATIENT_SESSION_KEY, None)

def has_active_patient(request):
    return request.session.get(ACTIVE_PATIENT_SESSION_KEY) is not None

def require_active_patient(request):
    patient = get_active_patient(request)
    if patient is None:
        raise ValueError("No active patient selected.")
    return patient

