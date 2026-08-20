from multiprocessing import context
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
import csv
from .forms import RegisterForm, PatientDataForm, VitalDetailsForm,PatientDataUpdateForm,VitalDetailsUpdateForm
from .models import PatientData, FormVitals,PredictionData,DQScore
from django.contrib.auth.forms import AuthenticationForm
from .forms import calculate_bmi,calculate_bmi_status
from .utils.dashboard_utils import calculate_health_metrics
from django.db.models.functions import TruncSecond
from django.utils import timezone
from .analytics.services import AnalyticsService
from .utils.clinical_workspace import get_active_patient, set_active_patient
from main_page.dashboard.services import get_dashboard_context
import logging

logger = logging.getLogger('main_page')

from django.core.cache import cache
cache.clear()


################## Registration View. ####################

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            messages.success(request, f"Account created for {user.username}!")
            return redirect('main_page:login_view')
    else:
        form = RegisterForm()
    
    return render(request, 'main_page/register.html', {'form': form})

############# Login View  #########################

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('main_page:home') #get_dashboard_redirect(user)
            else:
                messages.error(request, "Authentication failed. Django could not authenticate this user.")
    else:
        form = AuthenticationForm()
    return render(request, 'main_page/login.html', {'form': form})

############### Logout View ####################

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('main_page:login_view')  # Redirect to login page after logout

# view Vital Info

def view_vital_info(request):
    if request.user.is_authenticated:
        patient_data = get_active_patient(request)
        if not patient_data:
            messages.info(request, "Select a patient before viewing clinical data.")
            return redirect("main_page:patient_list")
        vitals = FormVitals.objects.filter(pid=patient_data.pid)
        return render(request, 'main_page/view_vital_info.html', {'vitals': vitals,'patient_data':patient_data})
    return redirect('main_page:login_view')  # Redirect if not authenticated


# update Vital Info

@login_required
def update_form_vitals(request):
        patient_data = get_active_patient(request)
        if not patient_data:
            messages.info(request, "Select a patient before updating vitals.")
            return redirect("main_page:patient_list")
        vitals_data = FormVitals.objects.filter(pid=patient_data.pid).first()

        if vitals_data is None:
            messages.info(request, 'No vitals data found. Please add your health information.')
            return redirect('main_page:enter_form_vitals')

        if request.method == 'POST':
            form = VitalDetailsUpdateForm(request.POST, instance=vitals_data)
            if form.is_valid():
                old_data = vitals_data
                new_vitals_data = FormVitals(
                    pid=old_data.pid,  # Assuming pid is a primary key or unique identifier
                    height=old_data.height,
                # Only update the specified fields
                    weight = form.cleaned_data['weight'] if form.cleaned_data['weight'] else old_data.weight,
                    heart_rate = form.cleaned_data['heart_rate'] if form.cleaned_data['heart_rate'] else old_data.heart_rate,
                    temperature = form.cleaned_data['temperature'] if form.cleaned_data['temperature'] else old_data.temperature,
                    respiration_rate = form.cleaned_data['respiration_rate'] if form.cleaned_data['respiration_rate'] else old_data.respiration_rate,
            )
            
            new_vitals_data.BMI = calculate_bmi(new_vitals_data.weight,new_vitals_data.height) if form.cleaned_data['weight'] else old_data.BMI
            new_vitals_data.BMI_status = calculate_bmi_status(new_vitals_data.BMI)
            new_vitals_data.save()

            messages.success(request, 'Your data has been updated successfully.')
            return redirect('main_page:view_vital_info')  # Redirect to home after success

        else:
                    form = VitalDetailsUpdateForm(instance=vitals_data)  # Populate the form with existing data

        return render(request, 'main_page/update_form_vitals.html', {'form': form})

#update patient data

@login_required
def update_patient_data(request):
    patient_data = get_active_patient(request)
    
    if patient_data is None:
        messages.info(request, 'Select a patient before editing their record.')
        return redirect('main_page:patient_list')

    if request.method == 'POST':
        form = PatientDataUpdateForm(request.POST, instance=patient_data)
        if form.is_valid():
           # if form.is_valid():
                form.save()  # Save the updated data directly
                messages.success(request, 'Your patient data has been updated successfully.')
        return redirect('main_page:home')
    else:
        form = PatientDataUpdateForm(instance=patient_data)  # Populate the form with existing data
    return render(request, 'main_page/update_patient_data.html', {'form': form})

# enter patient data view

@login_required
def enter_patient_data(request):
    if request.method == 'POST':
        form = PatientDataForm(request.POST)
        if form.is_valid():
            patient_data = form.save(commit=False)
            patient_data.user = request.user
            patient_data.save()
            set_active_patient(request, patient_data)
            messages.success(request, 'Patient record created and selected.')
            return redirect('main_page:enter_form_vitals')
    else:
        form = PatientDataForm()
    
    return render(request, 'main_page/enter_patient_data.html', {'form': form})

# enter vitals data view

@login_required
def enter_form_vitals(request):
    patient_data = get_active_patient(request)
    if not patient_data:
        messages.info(request, "Select a patient before recording vitals.")
        return redirect("main_page:patient_list")
    vitals_data = FormVitals.objects.filter(pid=patient_data).first()

    if request.method == 'POST':
        form = VitalDetailsForm(request.POST, instance=vitals_data)
        if form.is_valid():
            vitals_instance = form.save(commit=False)
            vitals_instance.pid = patient_data  # Assign the patient data
            vitals_instance.save()
            messages.success(request, 'Vital details updated successfully.')
            return redirect('main_page:home')
    else:
        form = VitalDetailsForm(instance=patient_data)

    return render(request, 'main_page/enter_form_vitals.html', {'form': form})

########### prediction data view ##############

@login_required
def view_prediction_data(request):
    # Get the first patient data for the logged-in user
    patient_data = get_active_patient(request)

    if not patient_data:
        messages.warning(request, "No patient data found.")
        return render(request, 'main_page/view_prediction_data.html', {
            'latest_results': [],
        })

    # Get all prediction data for the patient
    prediction_data = PredictionData.objects.filter(pid=patient_data)

    if not prediction_data.exists():
        messages.warning(request, "No prediction results found.")
        return render(request, 'main_page/view_prediction_data.html', {
            'latest_results': [],
        })

    # Group DQScore data by timestamp to the second
    dq_scores = DQScore.objects.filter(pid=patient_data).annotate(
        timestamp_rounded=TruncSecond('timestamp')
    ).values('timestamp_rounded', 'prediction_type', 'missing_features_count', 'total_features_count')

    # Combine prediction data with DQ scores based on matching timestamp and prediction type
    combined_data = (
        prediction_data
        .annotate(timestamp_rounded=TruncSecond('timestamp'))
        .values('prediction_type', 'prediction', 'diagnosis', 'timestamp_rounded', 'pid', 'timestamp')
    )

    results = []

    for prediction in combined_data:
        # Get corresponding DQScore for the current prediction
        dq_score = dq_scores.filter(
            prediction_type=prediction['prediction_type'],
            timestamp_rounded=prediction['timestamp_rounded']
        ).order_by('missing_features_count').first()

        if dq_score:
            results.append({
                'prediction_type': prediction['prediction_type'],
                'prediction': prediction['prediction'],
                'timestamp': prediction['timestamp'],
                'diagnosis': prediction['diagnosis'],
                'missing_features_count': dq_score['missing_features_count'],
                'total_features_count': dq_score['total_features_count'],
                'predtime': prediction['timestamp_rounded'],
            })

    # Filter results to keep the one with the least missing columns for each prediction type
    final_results = []
    seen_prediction_types = {}

    for result in results:
        pred_type = result['prediction_type']
        if pred_type not in seen_prediction_types or result['missing_features_count'] < seen_prediction_types[pred_type]['missing_features_count']:
            seen_prediction_types[pred_type] = result

    final_results = list(seen_prediction_types.values())

    return render(request, 'main_page/view_prediction_data.html', {
        'latest_results': final_results,
    })

###################### Prediction History View ####################

@login_required
def prediction_history(request):

    patient_data = get_active_patient(request)

    if not patient_data:
        messages.info(
            request,
            "Select a patient before viewing prediction history."
        )

        return redirect("main_page:patient_list")

    # ---------------------------------------------------------
    # Prediction history
    # ---------------------------------------------------------

    predictions = (
        PredictionData.objects
        .filter(pid=patient_data)
        .select_related("result")
        .order_by("-timestamp")
    )

    # ---------------------------------------------------------
    # Filter by prediction type
    # ---------------------------------------------------------

    prediction_type = request.GET.get("type", "").strip()

    if prediction_type:
        predictions = predictions.filter(
            prediction_type=prediction_type
        )

    # ---------------------------------------------------------
    # Summary metrics
    #
    # Keep these based on PredictionData for now.
    # We will migrate the risk KPI after validating the
    # standardized risk-level values across all modules.
    # ---------------------------------------------------------

    all_predictions = (
        PredictionData.objects
        .filter(pid=patient_data)
    )

    total_predictions = all_predictions.count()

    high_risk_count = all_predictions.filter(
        prediction="Yes"
    ).count()

    module_count = (
        all_predictions
        .values("prediction_type")
        .distinct()
        .count()
    )

    # ---------------------------------------------------------
    # Available modules
    # ---------------------------------------------------------

    available_modules = (
        all_predictions
        .values_list("prediction_type", flat=True)
        .distinct()
        .order_by("prediction_type")
    )

    # ---------------------------------------------------------
    # Context
    # ---------------------------------------------------------

    context = {
        "patient": patient_data,
        "predictions": predictions,
        "total_predictions": total_predictions,
        "high_risk_count": high_risk_count,
        "module_count": module_count,
        "available_modules": available_modules,
        "selected_type": prediction_type,
    }

    return render(
        request,
        "prediction/components/prediction_history.html",
        context,
    )

############### Prediction History details view ####################

@login_required
def prediction_history_detail(request, prediction_id):
    """Display a standardized historical AI prediction result."""

    patient_data = get_active_patient(request)

    if not patient_data:
        messages.info(
            request,
            "Select a patient before viewing prediction results."
        )
        return redirect("main_page:patient_list")

    prediction = (
        PredictionData.objects
        .filter(
            pk=prediction_id,
            pid=patient_data,
        )
        .select_related("result")
        .first()
    )

    if not prediction:
        messages.error(
            request,
            "Prediction record not found."
        )
        return redirect("main_page:prediction_history")

    if not hasattr(prediction, "result"):
        messages.warning(
            request,
            "This historical prediction does not have a standardized result."
        )
        return redirect("main_page:prediction_history")

    module_names = {
        "heart": "Heart Disease",
        "kidney": "Kidney Disease",
        "liver": "Liver Disease",
        "lungs": "Lung Disease",
        "lung_cancer": "Lung Cancer",
        "fitness": "Physical Fitness",
        "pancreas": "Diabetes",
    }

    module_icons = {
        "heart": "bi-heart-pulse",
        "kidney": "bi-droplet-half",
        "liver": "bi-activity",
        "lungs": "bi-lungs",
        "lung_cancer": "bi-lungs",
        "fitness": "bi-person-walking",
        "pancreas": "bi-droplet",
    }

    prediction_type = prediction.prediction_type

    context = {
        "patient": patient_data,
        "prediction": prediction,
        "prediction_result": prediction.result,

        "prediction_metadata": {
            "module_name": module_names.get(
                prediction_type,
                prediction_type.replace("_", " ").title(),
            ),
            "module_icon": module_icons.get(
                prediction_type,
                "bi-cpu",
            ),
            "model_name": (
                prediction.result.model_metadata.get("model_name")
                if prediction.result.model_metadata
                else "AI Prediction Model"
            ),
        },

        "is_fitness": prediction_type == "fitness",
    }

    return render(
        request,
        "prediction/history_result.html",
        context,
    )

############### Home View ####################

@login_required
def home(request):

    # ----------------------------------------------------
    # Patient
    # ----------------------------------------------------

    patient_data = get_active_patient(request)

    if not patient_data:

        messages.info(request, "Select a patient from the Clinical Workspace to view their dashboard.")

        return render(
            request,
            "dashboard/home.html",
            {
                "patient": None,
                "latest_results": [],
            },
        )

    # ----------------------------------------------------
    # Prediction Data
    # ----------------------------------------------------

    prediction_data = PredictionData.objects.filter(pid=patient_data)

    if not prediction_data.exists():

        messages.warning(request, "No prediction results found.")

        return render(
            request,
            "dashboard/home.html",
            {
                "patient": patient_data,
                "latest_results": [],
            },
        )

    # ----------------------------------------------------
    # DQ Scores
    # ----------------------------------------------------

    dq_scores = (
        DQScore.objects.filter(pid=patient_data)
        .annotate(
            timestamp_rounded=TruncSecond("timestamp")
        )
        .values(
            "timestamp_rounded",
            "prediction_type",
            "missing_features_count",
            "total_features_count",
        )
    )

    predictions = (
        prediction_data
        .annotate(
            timestamp_rounded=TruncSecond("timestamp")
        )
        .values(
            "prediction_type",
            "prediction",
            "diagnosis",
            "timestamp",
            "timestamp_rounded",
        )
    )

    # ----------------------------------------------------
    # Best Prediction Per Disease
    # ----------------------------------------------------

    best_predictions = {}

    for prediction in predictions:

        dq_score = (
            dq_scores.filter(
                prediction_type=prediction["prediction_type"],
                timestamp_rounded=prediction["timestamp_rounded"],
            )
            .order_by("missing_features_count")
            .first()
        )

        if not dq_score:
            continue

        disease = prediction["prediction_type"]

        if disease not in best_predictions:

            best_predictions[disease] = {
                "prediction": prediction,
                "dq_score": dq_score,
            }

        elif (
            dq_score["missing_features_count"]
            < best_predictions[disease]["dq_score"]["missing_features_count"]
        ):

            best_predictions[disease] = {
                "prediction": prediction,
                "dq_score": dq_score,
            }

    # ----------------------------------------------------
    # Dashboard Metrics
    # ----------------------------------------------------

    results = calculate_health_metrics(best_predictions)

    logger.debug("Dashboard Metrics: %s", results)

    # ----------------------------------------------------
    # Dashboard
    # ----------------------------------------------------

    return render(
        request,
        "dashboard/home.html",
        get_dashboard_context(request),)


# patient list view

@login_required
def patient_list(request):
    """List records managed by the signed-in healthcare professional."""

    patients = PatientData.objects.filter(user=request.user).order_by("lname", "fname")
    return render(
        request,
        "dashboard/patients.html",
        {"patients": patients, "active_patient": get_active_patient(request)},
    )

# select patient view

@login_required
def select_patient(request, patient_id):
    """Set a clinician-owned patient as the active workspace context."""

    patient = PatientData.objects.filter(id=patient_id, user=request.user).first()
    if not patient:
        messages.error(request, "That patient record is unavailable.")
        return redirect("main_page:patient_list")

    set_active_patient(request, patient)
    messages.success(request, f"{patient.fname} {patient.lname} is now the active patient.")
    return redirect("main_page:home")


#@login_required
#def analytics_dashboard(request):
    """
        Enterprise Analytics Dashboard.

        Intended for administrators, clinics and researchers.
    """
#    service = AnalyticsService()

#    context = service.dashboard_context()

#    print("Prediction Trend:", context.get("prediction_trend"))
#    print("Prediction Trend Type:", type(context.get("prediction_trend")))

#    return render(
#            request,
#            "dashboard/components/analytics.html",
#            context,
#    )

################### Analytics Views ####################

@login_required
def analytics_dashboard(request):
    service = AnalyticsService()

    context = service.dashboard_context()

    return render(
        request,
        "dashboard/components/analytics.html",
        context,
    )

#################### Analytics Export View ####################

@login_required
def analytics_export(request):
    """Download a CSV report containing aggregate analytics only."""

    timestamp = timezone.now().strftime("%Y%m%d")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="intellicare-analytics-{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow(["IntelliCareAI Enterprise Analytics Report"])
    writer.writerow(["Generated", timezone.localtime().strftime("%d %b %Y, %H:%M")])
    writer.writerow([])
    writer.writerow(["Section", "Metric", "Value"])
    writer.writerows(AnalyticsService.export_report())

    return response
