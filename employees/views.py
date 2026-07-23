from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.object_permissions import (
    check_employee_object_permission,
)

from .models import SalaryHistory
from audit.mixins import AuditViewSetMixin
from .serializers import (
    FinancialProfileSerializer,
    SalaryHistorySerializer,
    SalaryAdjustmentSerializer,
)
from .services import adjust_employee_salary
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from audit.services import log_activity
from audit.utils import get_client_ip
from accounts.permissions import RequiredPermission
from accounts.object_permissions import (
    check_employee_object_permission,
)
from accounts.scopes import (
    scope_employee_queryset,
    scope_related_employee_queryset,
)

from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeWorkExperience,
    EmployeeDependant,
    EmployeeCertification,
    EmployeeSkill,
    EmployeeBankAccount,
    EmployeeAsset,
)
from .serializers import (
    EmployeeSerializer,
    EmployeeDocumentSerializer,
    EmployeeEducationSerializer,
    EmployeeWorkExperienceSerializer,
    EmployeeDependantSerializer,
    EmployeeCertificationSerializer,
    EmployeeSkillSerializer,
    EmployeeBankAccountSerializer,
    EmployeeAssetSerializer,
)


class EmployeeViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "EMPLOYEES"

    serializer_class = EmployeeSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "employee_number",
        "first_name",
        "middle_name",
        "last_name",
        "personal_email",
        "work_email",
        "phone_number",
        "national_id_number",
        "tax_pin",
    ]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    filterset_fields = [
        "department",
        "branch",
        "employment_status",
    ]

    def get_permissions(self):
        permission_map = {
            "list": "employees.view",
            "retrieve": "employees.view",
            "create": "employees.create",
            "update": "employees.update",
            "partial_update": "employees.update",
            "destroy": "employees.delete",
        }

        permission_codename = permission_map.get(
            self.action,
            "employees.view",
        )

        return [
            RequiredPermission(permission_codename)()
        ]

    def get_queryset(self):
        queryset = Employee.objects.select_related(
            "user",
            "branch",
            "department",
            "designation",
            "manager",
        ).prefetch_related(
            "documents",
            "skills",
            "certifications",
            "dependants",
            "education",
            "bank_accounts",
            "assets",
        ).order_by("employee_number")

        return scope_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            permission_codename="employees.view",
        )

    def get_object(self):
        employee = super().get_object()

        permission_map = {
            "retrieve": "employees.view",
            "update": "employees.update",
            "partial_update": "employees.update",
            "destroy": "employees.delete",
        }

        permission = permission_map.get(
            self.action,
            "employees.view",
        )

        check_employee_object_permission(
            self.request.user,
            employee,
            permission,
        )

        return employee

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        employee = serializer.save()

        log_activity(
            user=request.user,
            action="CREATE",
            module="Employees",
            description=(
                f"Created employee "
                f"{employee.employee_number}."
            ),
            object_id=employee.id,
            ip_address=get_client_ip(request),
        )

        headers = self.get_success_headers(
            serializer.data
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeDocument.objects.select_related(
            "employee"
        ).order_by("-uploaded_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeEducationViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeEducationSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeEducation.objects.select_related(
            "employee"
        ).order_by("-end_date")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeWorkExperienceViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeWorkExperienceSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeWorkExperience.objects.select_related(
            "employee"
        ).order_by("-end_date")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeDependantViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeDependantSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeDependant.objects.select_related(
            "employee"
        ).order_by("full_name")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeCertificationViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeCertificationSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeCertification.objects.select_related(
            "employee"
        ).order_by("-issue_date")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeSkillViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSkillSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeSkill.objects.select_related(
            "employee"
        ).order_by("skill_name")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeBankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeBankAccountSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeBankAccount.objects.select_related(
            "employee"
        ).order_by("bank_name")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )


class EmployeeAssetViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeAssetSerializer
    permission_classes = [
        RequiredPermission("employees.view")
    ]

    def get_queryset(self):
        queryset = EmployeeAsset.objects.select_related(
            "employee"
        ).order_by("asset_name")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="employees.view",
        )
@extend_schema(
    responses={200: FinancialProfileSerializer},
    tags=["Employee Financial Profile"],
)
class EmployeeFinancialProfileView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            codename = "salary.view"
        else:
            codename = "salary.adjust"

        return [RequiredPermission(codename)()]

    def get_employee(self, request, employee_id, permission_codename):
        employee = Employee.objects.select_related(
            "branch",
            "department",
            "designation",
        ).get(id=employee_id)

        check_employee_object_permission(
            request.user,
            employee,
            permission_codename,
        )

        return employee

    def get(self, request, employee_id):
        try:
            employee = self.get_employee(
                request,
                employee_id,
                "salary.view",
            )

        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FinancialProfileSerializer(
            employee
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, employee_id):
        try:
            employee = self.get_employee(
                request,
                employee_id,
                "salary.adjust",
            )

        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FinancialProfileSerializer(
            employee,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_activity(
            user=request.user,
            action="UPDATE",
            module="Employees",
            description=(
                f"Updated financial profile for "
                f"{employee.employee_number}."
            ),
            object_id=employee.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@extend_schema(
    responses={200: SalaryHistorySerializer(many=True)},
    tags=["Employee Financial Profile"],
)
class EmployeeSalaryHistoryView(APIView):
    permission_classes = [
        RequiredPermission("salary.view")
    ]

    def get(self, request, employee_id):
        try:
            employee = Employee.objects.get(
                id=employee_id
            )

        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        check_employee_object_permission(
            request.user,
            employee,
            "salary.view",
        )

        queryset = SalaryHistory.objects.filter(
            employee=employee,
        ).select_related(
            "changed_by",
        ).order_by(
            "-effective_date",
            "-created_at",
        )

        serializer = SalaryHistorySerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=SalaryAdjustmentSerializer,
    responses={201: SalaryHistorySerializer},
    tags=["Employee Financial Profile"],
)
class EmployeeSalaryAdjustmentView(APIView):
    permission_classes = [
        RequiredPermission("salary.adjust")
    ]

    def post(self, request, employee_id):
        serializer = SalaryAdjustmentSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            employee = Employee.objects.get(
                id=employee_id
            )

        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        check_employee_object_permission(
            request.user,
            employee,
            "salary.adjust",
        )

        try:
            history = adjust_employee_salary(
                employee=employee,
                new_salary=serializer.validated_data[
                    "new_salary"
                ],
                adjustment_type=serializer.validated_data[
                    "adjustment_type"
                ],
                effective_date=serializer.validated_data[
                    "effective_date"
                ],
                reason=serializer.validated_data[
                    "reason"
                ],
                changed_by=request.user,
                update_active_contract=(
                    serializer.validated_data[
                        "update_active_contract"
                    ]
                ),
                request=request,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": (
                    "Employee salary adjusted successfully."
                ),
                "salary_history": SalaryHistorySerializer(
                    history
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )
