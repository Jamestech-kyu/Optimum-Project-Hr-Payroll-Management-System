from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import RequiredPermission
from audit.mixins import AuditViewSetMixin
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    BenefitPlan,
    EmployeeBenefit,
    BenefitContributionHistory,
    EnrollmentWindow,
)
from .serializers import (
    BenefitPlanSerializer,
    EmployeeBenefitSerializer,
    BenefitContributionHistorySerializer,
    EnrollmentWindowSerializer,
    EnrollBenefitSerializer,
    BenefitApprovalSerializer,
)
from .services import (
    approve_employee_benefit,
    enroll_employee,
    reject_employee_benefit,
)


class BenefitPlanViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "BENEFITS"

    queryset = BenefitPlan.objects.all()
    serializer_class = BenefitPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class EnrollmentWindowViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "BENEFITS"

    queryset = EnrollmentWindow.objects.all()
    serializer_class = EnrollmentWindowSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmployeeBenefitViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "BENEFITS"

    queryset = EmployeeBenefit.objects.select_related(
        "employee",
        "benefit_plan",
    )
    serializer_class = EmployeeBenefitSerializer
    permission_classes = [permissions.IsAuthenticated]


class BenefitContributionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BenefitContributionHistory.objects.select_related(
        "employee_benefit",
        "employee_benefit__employee",
    )
    serializer_class = BenefitContributionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    request=EnrollBenefitSerializer,
    responses={201: EmployeeBenefitSerializer},
    tags=["Benefits"],
)
class EnrollEmployeeBenefitView(APIView):
    permission_classes = [
        RequiredPermission("benefits.enroll")
    ]

    def post(self, request):
        serializer = EnrollBenefitSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        enrollment = enroll_employee(
            employee_id=serializer.validated_data["employee_id"],
            benefit_plan_id=serializer.validated_data["benefit_plan_id"],
            enrollment_date=serializer.validated_data["enrollment_date"],
            effective_date=serializer.validated_data["effective_date"],
            end_date=serializer.validated_data.get("end_date"),
            employee_amount=serializer.validated_data["employee_amount"],
            employer_amount=serializer.validated_data["employer_amount"],
            remarks=serializer.validated_data.get("remarks", ""),
            created_by=request.user,
        )

        log_activity(
            user=request.user,
            action="CREATE",
            module="Benefits",
            description=(
                f"Enrolled employee "
                f"{enrollment.employee.employee_number} "
                f"into {enrollment.benefit_plan.name}."
            ),
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Employee enrolled successfully.",
                "enrollment": EmployeeBenefitSerializer(
                    enrollment
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=BenefitApprovalSerializer,
    responses={200: EmployeeBenefitSerializer},
    tags=["Benefits"],
)
class ApproveEmployeeBenefitView(APIView):
    permission_classes = [
        RequiredPermission("benefits.approve")
    ]

    def post(self, request, enrollment_id):
        serializer = BenefitApprovalSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        enrollment = get_object_or_404(
            EmployeeBenefit.objects.select_related(
                "employee",
                "benefit_plan",
            ),
            id=enrollment_id,
        )

        enrollment = approve_employee_benefit(
            enrollment=enrollment,
            approved_by=request.user,
            remarks=serializer.validated_data.get(
                "remarks",
                "",
            ),
        )

        log_activity(
            user=request.user,
            action="APPROVE",
            module="Benefits",
            description=(
                f"Approved {enrollment.benefit_plan.name} "
                f"for employee "
                f"{enrollment.employee.employee_number}."
            ),
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": (
                    "Benefit enrollment approved successfully."
                ),
                "enrollment": EmployeeBenefitSerializer(
                    enrollment
                ).data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=BenefitApprovalSerializer,
    responses={200: EmployeeBenefitSerializer},
    tags=["Benefits"],
)
class RejectEmployeeBenefitView(APIView):
    permission_classes = [
        RequiredPermission("benefits.approve")
    ]

    def post(self, request, enrollment_id):
        serializer = BenefitApprovalSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        enrollment = get_object_or_404(
            EmployeeBenefit.objects.select_related(
                "employee",
                "benefit_plan",
            ),
            id=enrollment_id,
        )

        enrollment = reject_employee_benefit(
            enrollment=enrollment,
            approved_by=request.user,
            remarks=serializer.validated_data.get(
                "remarks",
                "",
            ),
        )

        log_activity(
            user=request.user,
            action="REJECT",
            module="Benefits",
            description=(
                f"Rejected {enrollment.benefit_plan.name} "
                f"for employee "
                f"{enrollment.employee.employee_number}."
            ),
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": (
                    "Benefit enrollment rejected successfully."
                ),
                "enrollment": EmployeeBenefitSerializer(
                    enrollment
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class EmployeeBenefitsView(APIView):
    permission_classes = [
        RequiredPermission("benefits.view")
    ]

    def get(self, request, employee_id):
        queryset = EmployeeBenefit.objects.filter(
            employee_id=employee_id,
        ).select_related(
            "benefit_plan",
        )

        serializer = EmployeeBenefitSerializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)
