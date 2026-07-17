from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from departments.urls import router as departments_router

api_router = DefaultRouter()
api_router.registry.extend(departments_router.registry)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Authentication APIs
    path("api/auth/", include("accounts.urls")),

    # Employee and Department APIs
    path("api/", include("employees.urls")),
    path("api/benefits/", include("benefits.urls")),
    path("api/", include(api_router.urls)),
    path("api/attendance/", include("attendance.urls")),
    path("api/", include("contracts.urls")),
    path("api/leave/", include("leave_management.urls")),
    path("api/payroll/", include("payroll.urls")),
    path("api/hr-operations/", include("hr_operations.urls")),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
