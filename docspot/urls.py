"""
URL configuration for docspot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Landing page
    path("", TemplateView.as_view(template_name="landing.html"), name="landing"),

    # Authentication & dashboard
    path("", include("main_page.urls")),

    # Prediction apps
    path("heart/", include("heart.urls")),
    path("kidney/", include("kidney.urls")),
    path("liver/", include("liver.urls")),
    path("lungs/", include("lungs.urls")),
    path("pancreas/", include("pancreas.urls")),
    path("fitness/", include("fitness.urls")),
    path("lung_cancer/", include("lung_cancer.urls")),

    # API
    path("api/", include("main_page.api_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]