from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Authentication APIs
    path("api/auth/", include("accounts.urls")),

    # Employee APIs
    path("api/", include("employees.urls")),
    path("api/attendance/", include("attendance.urls")),
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
