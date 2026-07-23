from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceDashboardView,
    DashboardOverviewView,
    EmployeeDashboardView,
    GenerateReportView,
    LeaveDashboardView,
    PayrollDashboardView,
    PerformanceDashboardView,
    PreviewReportView,
    ReportExecutionViewSet,
    ReportSummaryView,
    ReportTemplateViewSet,
    RoleDashboardView,
    SavedReportViewSet,
    TrainingDashboardView,
)

router = DefaultRouter()

router.register(
    "templates",
    ReportTemplateViewSet,
    basename="report-templates",
)
router.register(
    "executions",
    ReportExecutionViewSet,
    basename="report-executions",
)
router.register(
    "saved",
    SavedReportViewSet,
    basename="saved-reports",
)

urlpatterns = [
    path(
        "generate/",
        GenerateReportView.as_view(),
        name="generate-report",
    ),
    path(
        "preview/",
        PreviewReportView.as_view(),
        name="preview-report",
    ),
    path(
        "summary/",
        ReportSummaryView.as_view(),
        name="report-summary",
    ),
    path(
        "dashboard/overview/",
        DashboardOverviewView.as_view(),
        name="dashboard-overview",
    ),
    path(
        "dashboard/employees/",
        EmployeeDashboardView.as_view(),
        name="dashboard-employees",
    ),
    path(
        "dashboard/attendance/",
        AttendanceDashboardView.as_view(),
        name="dashboard-attendance",
    ),
    path(
        "dashboard/leave/",
        LeaveDashboardView.as_view(),
        name="dashboard-leave",
    ),
    path(
        "dashboard/payroll/",
        PayrollDashboardView.as_view(),
        name="dashboard-payroll",
    ),
    path(
        "dashboard/performance/",
        PerformanceDashboardView.as_view(),
        name="dashboard-performance",
    ),
    path(
        "dashboard/training/",
        TrainingDashboardView.as_view(),
        name="dashboard-training",
    ),
    path(
        "dashboard/my-dashboard/",
        RoleDashboardView.as_view(),
        name="role-dashboard",
    ),
    path("", include(router.urls)),
]
