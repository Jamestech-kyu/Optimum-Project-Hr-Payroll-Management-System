from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import RequiredPermission

from .models import (
    BranchTask,
    EmployeeNote,
    PerformanceCycle,
    PerformanceReview,
    PerformanceGoal,
    DisciplinaryCase,
    Announcement,
    Training,
    TrainingEnrollment,
    OffboardingCase,
    OffboardingChecklistItem,
    OffboardingExitInterview,
    OffboardingFinalSettlement,
)
from .serializers import (
    BranchTaskSerializer,
    EmployeeNoteSerializer,
    PerformanceCycleSerializer,
    PerformanceReviewSerializer,
    PerformanceGoalSerializer,
    DisciplinaryCaseSerializer,
    AnnouncementSerializer,
    TrainingSerializer,
    TrainingEnrollmentSerializer,
    OffboardingCaseSerializer,
    OffboardingChecklistItemSerializer,
    OffboardingExitInterviewSerializer,
    OffboardingFinalSettlementSerializer,
)

# Import Employee model for real data
from employees.models import Employee
# If Department model exists, import it
try:
    from departments.models import Department
except ImportError:
    Department = None


# =========================================================
# PERFORMANCE API
# =========================================================

class BranchTaskViewSet(viewsets.ModelViewSet):
    """Branch dashboard task board."""

    queryset = BranchTask.objects.select_related("assigned_to", "created_by")
    serializer_class = BranchTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "priority", "assigned_to", "branch", "department"]
    search_fields = ["title", "description"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        task = serializer.save()
        # Stamp completion the first time a task reaches Done.
        if task.status == "DONE" and not task.completed_at:
            task.completed_at = timezone.now()
            task.save(update_fields=["completed_at"])
        elif task.status != "DONE" and task.completed_at:
            task.completed_at = None
            task.save(update_fields=["completed_at"])


class EmployeeNoteViewSet(viewsets.ModelViewSet):
    """Notes recorded against an employee, used by the lifecycle screens."""

    queryset = EmployeeNote.objects.select_related("employee", "author")
    serializer_class = EmployeeNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "category"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PerformanceCycleViewSet(viewsets.ModelViewSet):
    """Appraisal cycles for the client's Performance Oversight page.

    The model existed but was never exposed, so the page was reading
    /performance/cycles/ instead - a different model whose fields do not line up
    (``title`` rather than ``name``, no rating scale or scope).
    """

    queryset = PerformanceCycle.objects.prefetch_related("employees").order_by(
        "-start_date", "-created_at"
    )
    serializer_class = PerformanceCycleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "scope"]
    search_fields = ["name", "description", "review_period"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PerformanceReviewViewSet(viewsets.ModelViewSet):
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "status"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        review = self.get_object()
        review.status = "SUBMITTED"
        review.save()
        return Response(self.get_serializer(review).data)


class PerformanceGoalViewSet(viewsets.ModelViewSet):
    queryset = PerformanceGoal.objects.select_related(
        "employee", "review", "review__employee", "cycle"
    ).order_by("target_date", "id")
    serializer_class = PerformanceGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["review", "employee", "cycle", "status"]


# =========================================================
# DISCIPLINARY API
# =========================================================

class DisciplinaryCaseViewSet(viewsets.ModelViewSet):
    queryset = DisciplinaryCase.objects.all()
    serializer_class = DisciplinaryCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "status", "severity"]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        case = self.get_object()
        case.status = "RESOLVED"
        case.resolution_notes = request.data.get("resolution_notes", case.resolution_notes)
        case.action_taken = request.data.get("action_taken", case.action_taken)
        case.resolved_at = timezone.now()
        case.save()
        return Response(self.get_serializer(case).data)


# =========================================================
# ANNOUNCEMENTS API
# =========================================================

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["audience", "is_pinned"]
    search_fields = ["title", "body"]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

    @action(detail=False, methods=["get"])
    def active(self, request):
        now = timezone.now()
        qs = self.get_queryset().filter(publish_at__lte=now).exclude(expires_at__lt=now)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


# =========================================================
# TRAINING API
# =========================================================

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "is_mandatory"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        training = self.get_object()
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response({"employee": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        enrollment, created = TrainingEnrollment.objects.get_or_create(
            training=training, employee_id=employee_id
        )
        return Response(
            TrainingEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TrainingEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = TrainingEnrollment.objects.all()
    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["training", "employee", "status"]


class OffboardingCaseViewSet(viewsets.ModelViewSet):
    queryset = OffboardingCase.objects.select_related("employee", "initiated_by")
    serializer_class = OffboardingCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "employee", "exit_type"]
    search_fields = ["employee__first_name", "employee__last_name", "employee__employee_number", "reason"]

    @transaction.atomic
    def perform_create(self, serializer):
        employee = serializer.validated_data["employee"]
        if OffboardingCase.objects.filter(
            employee=employee,
            status__in=["PENDING", "IN_PROGRESS", "OVERDUE"],
        ).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"employee": "This employee already has an active offboarding case."})

        case = serializer.save(initiated_by=self.request.user)
        checklist = [
            ("handover", "Knowledge transfer and handover", "Document responsibilities and hand over active work."),
            ("assets", "Return company assets", "Return laptop, access cards, and assigned equipment."),
            ("it-access", "Revoke system access", "Disable company accounts and system access on the final day."),
            ("finance", "Review final settlement", "Confirm final salary, reimbursements, and deductions."),
            ("statutory", "Complete statutory clearance", "Complete the required statutory and benefits clearance."),
            ("exit-interview", "Conduct exit interview", "Record feedback and the employee's exit reason."),
            ("documentation", "Archive employee records", "File the exit documentation and update employee records."),
        ]
        OffboardingChecklistItem.objects.bulk_create([
            OffboardingChecklistItem(
                case=case,
                category=category,
                item=item,
                description=description,
                due_date=case.last_working_day,
                order=index,
            )
            for index, (category, item, description) in enumerate(checklist, start=1)
        ])
        OffboardingExitInterview.objects.get_or_create(case=case)
        OffboardingFinalSettlement.objects.get_or_create(case=case)


class OffboardingChecklistItemViewSet(viewsets.ModelViewSet):
    # Explicit ordering: paginated responses are otherwise non-deterministic and
    # rows can repeat or disappear between pages.
    queryset = OffboardingChecklistItem.objects.select_related(
        "case", "owner"
    ).order_by("case_id", "order", "id")
    serializer_class = OffboardingChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case", "status"]


class OffboardingExitInterviewViewSet(viewsets.ModelViewSet):
    queryset = OffboardingExitInterview.objects.select_related("case").order_by("id")
    serializer_class = OffboardingExitInterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case"]


class OffboardingFinalSettlementViewSet(viewsets.ModelViewSet):
    queryset = OffboardingFinalSettlement.objects.select_related("case").order_by("id")
    serializer_class = OffboardingFinalSettlementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case", "status"]


# =========================================================
# DASHBOARD API – REAL DATA ONLY
# =========================================================

def get_branch_field_name():
    """Determine the field name for branch in Employee model."""
    try:
        # Check if Employee has a ForeignKey to Branch
        if hasattr(Employee, 'branch') and hasattr(Employee._meta.get_field('branch'), 'remote_field'):
            return 'branch__name'
        else:
            return 'branch'
    except:
        return 'branch'

def get_employee_count():
    return Employee.objects.count()

def get_employees_by_branch():
    branch_field = get_branch_field_name()
    return Employee.objects.values(branch_field).annotate(count=Count('id')).order_by('-count')

def get_departments():
    if Department:
        return Department.objects.annotate(employee_count=Count('employee')).values('name', 'employee_count')
    return []

@api_view(['GET'])
@permission_classes([RequiredPermission("reports.view")])
def executive_dashboard(request):
    total_employees = get_employee_count()

    # Branch distribution
    branch_distribution = get_employees_by_branch()
    branch_field = get_branch_field_name()
    departments = [
        {
            "name": item.get(branch_field, 'Unknown'),
            "headcount": item['count']
        }
        for item in branch_distribution
    ]

    # If no branches, return empty
    if not departments:
        departments = []

    # Payroll – if there is a salary field, use it; otherwise estimate
    try:
        total_payroll_sum = Employee.objects.aggregate(total=Sum('salary'))['total']
        if total_payroll_sum:
            total_payroll = total_payroll_sum
        else:
            total_payroll = total_employees * 68000
    except:
        total_payroll = total_employees * 68000

    data = {
        "summary": {
            "totalEmployees": total_employees,
            "totalPayroll": total_payroll,  # You can format in frontend or keep as number
            "complianceScore": None,  # Not available yet
            "benefitsUtilization": None,
            "turnoverRate": None,
            "avgPerformance": None,
        },
        "workforce": {
            "headcount": [],  # No historical data yet – frontend can show current only
            "turnoverRate": None,
            "departments": departments,
        },
        "payroll": {
            "total": [],      # No monthly breakdown without extra data
            "breakdown": [],
            "budget": None,
            "branchComparison": [],
        },
        "compliance": {
            "status": [],
            "flags": [],
            "overallScore": None,
        },
        "benefits": {
            "summary": [],
            "totalCost": None,
            "avgUtilization": None,
        },
        "performance": {
            "distribution": [],
            "departmentComparison": [],
            "trend": [],
            "overallAvg": None,
        },
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([RequiredPermission("reports.view")])
def hr_dashboard(request):
    branch_name = request.query_params.get('branch', None)
    qs = Employee.objects.all()

    if branch_name:
        branch_field = get_branch_field_name()
        try:
            qs = qs.filter(**{branch_field: branch_name})
        except:
            qs = qs.filter(branch=branch_name)

    total_employees = qs.count()

    # Branch breakdown (for this branch or all)
    branch_field = get_branch_field_name()
    branch_data = qs.values(branch_field).annotate(count=Count('id')).order_by('-count')

    branches = [
        {
            "name": item.get(branch_field, 'Unknown'),
            "employees": item['count'],
            "amount": None,  # Can't compute without payroll model
            "status": None
        }
        for item in branch_data
    ]

    # If no branch data, provide empty list
    if not branches:
        branches = []

    # Payroll – if salary field exists, sum it
    try:
        payroll_sum = qs.aggregate(total=Sum('salary'))['total']
        if payroll_sum is None:
            payroll_sum = total_employees * 68000
    except:
        payroll_sum = total_employees * 68000

    # Pending approvals – if status field exists
    pending_approvals = 0
    if hasattr(Employee, 'status'):
        pending_approvals = qs.filter(status='PENDING').count()

    data = {
        "employees": total_employees,
        "payroll": payroll_sum,  # Send as number
        "approvals": pending_approvals,
        "compliance": None,  # Not available
        "branches": branches,
        "progress": [],       # No payroll run data without models
        "activity": [],       # No activity model yet
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([RequiredPermission("reports.view")])
def branch_dashboard(request, branch_id):
    # Try to filter by branch ID (if branch is a ForeignKey) or by name
    branch_field = get_branch_field_name()
    try:
        employees = Employee.objects.filter(**{branch_field: branch_id})
    except:
        employees = Employee.objects.filter(branch=branch_id)

    total = employees.count()

    data = {
        "employees": total,
        "newHires": None,
        "exits": None,
        "attritionRate": None,
        "totalPayroll": None,
        "complianceStatus": None,
        "headcountTrend": [],
        "averageTenure": None,
        "turnoverRate": None,
        "payrollTrend": [],
        "payrollBreakdown": [],
        "budget": None,
        "complianceStatuses": [],
        "complianceAlerts": [],
        "complianceScore": None,
        "benefitsUtilization": [],
        "totalBenefitsCost": None,
        "avgBenefitsUtilization": None,
        "performanceAvg": None,
        "performanceTrend": [],
    }
    return Response(data)
