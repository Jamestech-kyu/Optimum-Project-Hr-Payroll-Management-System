from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.services import log_activity
from audit.utils import get_client_ip

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
    queryset = Employee.objects.all().order_by("employee_number")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()

        log_activity(
            user=request.user,
            action="CREATE",
            module="Employees",
            description=f"Created employee {employee.employee_number}.",
            object_id=employee.id,
            ip_address=get_client_ip(request),
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.all().order_by("-uploaded_at")
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated]


class EmployeeEducationViewSet(viewsets.ModelViewSet):
    queryset = EmployeeEducation.objects.all().order_by("-end_date")
    serializer_class = EmployeeEducationSerializer
    permission_classes = [IsAuthenticated]


class EmployeeWorkExperienceViewSet(viewsets.ModelViewSet):
    queryset = EmployeeWorkExperience.objects.all().order_by("-end_date")
    serializer_class = EmployeeWorkExperienceSerializer
    permission_classes = [IsAuthenticated]


class EmployeeDependantViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDependant.objects.all().order_by("full_name")
    serializer_class = EmployeeDependantSerializer
    permission_classes = [IsAuthenticated]


class EmployeeCertificationViewSet(viewsets.ModelViewSet):
    queryset = EmployeeCertification.objects.all().order_by("-issue_date")
    serializer_class = EmployeeCertificationSerializer
    permission_classes = [IsAuthenticated]


class EmployeeSkillViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSkill.objects.all().order_by("skill_name")
    serializer_class = EmployeeSkillSerializer
    permission_classes = [IsAuthenticated]


class EmployeeBankAccountViewSet(viewsets.ModelViewSet):
    queryset = EmployeeBankAccount.objects.all().order_by("bank_name")
    serializer_class = EmployeeBankAccountSerializer
    permission_classes = [IsAuthenticated]


class EmployeeAssetViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAsset.objects.all().order_by("asset_name")
    serializer_class = EmployeeAssetSerializer
    permission_classes = [IsAuthenticated]