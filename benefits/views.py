from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import RequiredPermission
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
)
from .services import enroll_employee


class BenefitPlanViewSet(viewsets.ModelViewSet):
    queryset = BenefitPlan.objects.all()
    serializer_class = BenefitPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class EnrollmentWindowViewSet(viewsets.ModelViewSet):
    queryset = EnrollmentWindow.objects.all()
    serializer_class = EnrollmentWindowSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmployeeBenefitViewSet(viewsets.ModelViewSet):
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