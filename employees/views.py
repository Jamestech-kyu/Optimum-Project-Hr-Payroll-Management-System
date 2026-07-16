from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework import filters
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


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter]

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
