from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GenerateReportView,
    PreviewReportView,
    ReportExecutionViewSet,
    ReportSummaryView,
    ReportTemplateViewSet,
    SavedReportViewSet,
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
    path("", include(router.urls)),
]
