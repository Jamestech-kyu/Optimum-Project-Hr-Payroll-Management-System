from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from accounts.permissions import RequiredPermission

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .role_dashboard_services import get_role_dashboard

from .models import (
    ReportExecution,
    ReportTemplate,
    SavedReport,
    ScheduledReport,
)
from .analytics_services import (
    benefits_analytics,
    compliance_analytics,
    payroll_analytics,
    performance_analytics,
    workforce_analytics,
)
from .dashboard_services import (
    attendance_statistics,
    dashboard_overview,
    employee_statistics,
    leave_statistics,
    payroll_statistics,
    performance_statistics,
    training_statistics,
)
from .serializers import (
    ReportExecutionSerializer,
    ReportGenerationSerializer,
    ReportPreviewSerializer,
    ReportTemplateSerializer,
    SavedReportSerializer,
    ScheduledReportSerializer,
)
from .services import (
    create_report_execution,
    generate_report_data,
)
from .dashboard_services import (
    attendance_statistics,
    dashboard_overview,
    employee_statistics,
    leave_statistics,
    payroll_statistics,
    performance_statistics,
    training_statistics,
)

class ReportTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ReportTemplate.objects.all()

        report_type = self.request.query_params.get(
            "report_type"
        )
        is_active = self.request.query_params.get(
            "is_active"
        )

        if report_type:
            queryset = queryset.filter(
                report_type=report_type.upper()
            )

        if is_active is not None:
            queryset = queryset.filter(
                is_active=(
                    is_active.lower() == "true"
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )


class ScheduledReportViewSet(viewsets.ModelViewSet):
    """Recurring report schedules shown on the analytics page."""

    serializer_class = ScheduledReportSerializer
    permission_classes = [RequiredPermission("reports.view")]

    def get_queryset(self):
        return ScheduledReport.objects.all().order_by("name")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SavedReportViewSet(viewsets.ModelViewSet):
    serializer_class = SavedReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = SavedReport.objects.filter(
            owner=user
        )

        if user.is_staff:
            queryset = SavedReport.objects.filter(
                owner=user
            ) | SavedReport.objects.filter(
                is_public=True
            )

        report_type = self.request.query_params.get(
            "report_type"
        )

        if report_type:
            queryset = queryset.filter(
                report_type=report_type.upper()
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(
            owner=self.request.user
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="run",
    )
    def run_saved_report(self, request, pk=None):
        saved_report = self.get_object()

        template = ReportTemplate.objects.filter(
            report_type=saved_report.report_type,
            is_active=True,
        ).first()

        if not template:
            return Response(
                {
                    "detail": (
                        "No active template exists for "
                        "this report type."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution, data = create_report_execution(
            template_id=template.id,
            requested_by=request.user,
            export_format=saved_report.export_format,
            filters=saved_report.filters,
        )

        return Response(
            {
                "execution": ReportExecutionSerializer(
                    execution,
                    context={"request": request},
                ).data,
                "data": (
                    data
                    if execution.export_format == "JSON"
                    else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class ReportExecutionViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = ReportExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ReportExecution.objects.select_related(
            "template",
            "requested_by",
        )

        if not self.request.user.is_staff:
            queryset = queryset.filter(
                requested_by=self.request.user
            )

        status_value = self.request.query_params.get(
            "status"
        )
        report_type = self.request.query_params.get(
            "report_type"
        )
        export_format = self.request.query_params.get(
            "export_format"
        )

        if status_value:
            queryset = queryset.filter(
                status=status_value.upper()
            )

        if report_type:
            queryset = queryset.filter(
                template__report_type=report_type.upper()
            )

        if export_format:
            queryset = queryset.filter(
                export_format=export_format.upper()
            )

        return queryset

    @action(
        detail=True,
        methods=["get"],
        url_path="download",
    )
    def download(self, request, pk=None):
        execution = self.get_object()

        if execution.status != "COMPLETED":
            return Response(
                {
                    "detail": (
                        "This report has not completed "
                        "successfully."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not execution.generated_file:
            return Response(
                {
                    "detail": (
                        "This report has no downloadable file."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            execution.generated_file.open("rb"),
            as_attachment=True,
            filename=execution.generated_file.name.split(
                "/"
            )[-1],
        )


class GenerateReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReportGenerationSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        execution, data = create_report_execution(
            template_id=serializer.validated_data[
                "template_id"
            ],
            requested_by=request.user,
            export_format=serializer.validated_data.get(
                "export_format"
            ),
            filters=serializer.validated_data.get(
                "filters",
                {},
            ),
        )

        response_data = {
            "message": "Report generated successfully.",
            "execution": ReportExecutionSerializer(
                execution,
                context={"request": request},
            ).data,
        }

        if execution.export_format == "JSON":
            response_data["data"] = data

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )


class PreviewReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReportPreviewSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        report_type = serializer.validated_data[
            "report_type"
        ]
        filters = serializer.validated_data.get(
            "filters",
            {},
        )

        data = generate_report_data(
            report_type,
            filters,
        )

        return Response(
            {
                "report_type": report_type,
                "count": len(data),
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class ReportSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        executions = ReportExecution.objects.all()

        if not request.user.is_staff:
            executions = executions.filter(
                requested_by=request.user
            )

        return Response(
            {
                "total_reports": executions.count(),
                "pending": executions.filter(
                    status="PENDING"
                ).count(),
                "running": executions.filter(
                    status="RUNNING"
                ).count(),
                "completed": executions.filter(
                    status="COMPLETED"
                ).count(),
                "failed": executions.filter(
                    status="FAILED"
                ).count(),
            }
        )


class DashboardOverviewView(APIView):
    # Company-wide totals, so gated on reports.view rather than mere
    # authentication. Employees use dashboard/my-dashboard/ instead.
    permission_classes = [RequiredPermission("reports.view")]

    def get(self, request):
        return Response(
            dashboard_overview(),
            status=status.HTTP_200_OK,
        )


class AnalyticsDashboardView(APIView):
    """Base view for the Reports & Analytics cards in the web client.

    Subclasses supply ``analytics``, a callable taking the parsed filters. The
    client sends ``branch``/``department`` display names plus a date range; both
    the nested ``dateRange[start]`` form used by the analytics page and the flat
    ``start_date`` form are accepted.
    """

    permission_classes = [RequiredPermission("reports.view")]
    analytics = None

    def _filters(self, request):
        params = request.query_params

        def date_param(*names):
            for name in names:
                value = params.get(name)
                if value:
                    parsed = parse_date(value)
                    if parsed:
                        return parsed
            return None

        return {
            "branch": params.get("branch") or None,
            "department": params.get("department") or None,
            "start": date_param("start_date", "dateRange[start]", "start"),
            "end": date_param("end_date", "dateRange[end]", "end"),
        }

    def get(self, request):
        return Response(
            type(self).analytics(**self._filters(request)),
            status=status.HTTP_200_OK,
        )


class EmployeeDashboardView(AnalyticsDashboardView):
    analytics = staticmethod(workforce_analytics)


class AttendanceDashboardView(APIView):
    permission_classes = [RequiredPermission("reports.view")]

    def get(self, request):
        return Response(
            attendance_statistics(),
            status=status.HTTP_200_OK,
        )


class LeaveDashboardView(APIView):
    permission_classes = [RequiredPermission("reports.view")]

    def get(self, request):
        return Response(
            leave_statistics(),
            status=status.HTTP_200_OK,
        )


class PayrollDashboardView(AnalyticsDashboardView):
    analytics = staticmethod(payroll_analytics)


class ComplianceDashboardView(AnalyticsDashboardView):
    analytics = staticmethod(compliance_analytics)


class BenefitsDashboardView(AnalyticsDashboardView):
    analytics = staticmethod(benefits_analytics)


class PerformanceDashboardView(AnalyticsDashboardView):
    analytics = staticmethod(performance_analytics)


class TrainingDashboardView(APIView):
    permission_classes = [RequiredPermission("reports.view")]

    def get(self, request):
        return Response(
            training_statistics(),
            status=status.HTTP_200_OK,
        )
class RoleDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            get_role_dashboard(request.user),
            status=status.HTTP_200_OK,
        )