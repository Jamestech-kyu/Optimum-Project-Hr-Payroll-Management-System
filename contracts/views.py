from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.object_permissions import (
    check_related_employee_permission,
)
from accounts.permissions import RequiredPermission
from accounts.scopes import scope_related_employee_queryset
from audit.mixins import AuditViewSetMixin
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    EmploymentContract,
    ContractRenewal,
    ContractTermination,
)
from .serializers import (
    EmploymentContractSerializer,
    ContractRenewalSerializer,
    ContractTerminationSerializer,
    ContractRenewActionSerializer,
    ContractTerminateActionSerializer,
)
from .services import (
    renew_contract,
    terminate_contract,
)


class EmploymentContractViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "CONTRACTS"

    serializer_class = EmploymentContractSerializer

    def get_permissions(self):
        permission_map = {
            "list": "contracts.view",
            "retrieve": "contracts.view",
            "create": "contracts.create",
            "update": "contracts.update",
            "partial_update": "contracts.update",
            "destroy": "contracts.terminate",
        }

        codename = permission_map.get(
            self.action,
            "contracts.view",
        )

        return [RequiredPermission(codename)()]

    def get_queryset(self):
        queryset = EmploymentContract.objects.select_related(
            "employee",
            "employee__branch",
            "employee__department",
            "created_by",
            "approved_by",
        ).order_by("-start_date", "-created_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="contracts.view",
        )

    def get_object(self):
        permission_map = {
            "retrieve": "contracts.view",
            "update": "contracts.update",
            "partial_update": "contracts.update",
            "destroy": "contracts.terminate",
        }

        codename = permission_map.get(
            self.action,
            "contracts.view",
        )

        return check_related_employee_permission(
            user=self.request.user,
            queryset=EmploymentContract.objects.select_related(
                "employee",
            ),
            employee_field="employee",
            object_id=self.kwargs["pk"],
            permission_codename=codename,
        )

    def perform_create(self, serializer):
        contract = serializer.save(
            created_by=self.request.user,
        )

        log_activity(
            user=self.request.user,
            action="CREATE",
            module="Contracts",
            description=(
                f"Created contract {contract.contract_number} "
                f"for employee {contract.employee.employee_number}."
            ),
            object_id=contract.id,
            ip_address=get_client_ip(self.request),
        )


class ContractRenewalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContractRenewalSerializer
    permission_classes = [
        RequiredPermission("contracts.view")
    ]

    def get_queryset(self):
        queryset = ContractRenewal.objects.select_related(
            "contract",
            "contract__employee",
            "renewed_by",
        ).order_by("-renewed_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="contract__employee",
            permission_codename="contracts.view",
        )


class ContractTerminationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContractTerminationSerializer
    permission_classes = [
        RequiredPermission("contracts.view")
    ]

    def get_queryset(self):
        queryset = ContractTermination.objects.select_related(
            "contract",
            "contract__employee",
            "terminated_by",
        ).order_by("-created_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="contract__employee",
            permission_codename="contracts.view",
        )


@extend_schema(
    responses={200: EmploymentContractSerializer(many=True)},
    tags=["Contracts"],
)
class ExpiringContractsView(APIView):
    permission_classes = [
        RequiredPermission("contracts.view")
    ]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            return Response(
                {"message": "Days must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if days < 0 or days > 365:
            return Response(
                {
                    "message": (
                        "Days must be between 0 and 365."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.localdate()
        end_date = today + timedelta(days=days)

        queryset = EmploymentContract.objects.filter(
            status="ACTIVE",
            end_date__isnull=False,
            end_date__range=(today, end_date),
        ).select_related(
            "employee",
            "employee__branch",
            "employee__department",
        )

        queryset = scope_related_employee_queryset(
            user=request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="contracts.view",
        )

        serializer = EmploymentContractSerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=ContractRenewActionSerializer,
    responses={200: ContractRenewalSerializer},
    tags=["Contracts"],
)
class RenewContractView(APIView):
    permission_classes = [
        RequiredPermission("contracts.renew")
    ]

    def post(self, request, contract_id):
        serializer = ContractRenewActionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            contract = check_related_employee_permission(
                user=request.user,
                queryset=EmploymentContract.objects.select_related(
                    "employee",
                ),
                employee_field="employee",
                object_id=contract_id,
                permission_codename="contracts.renew",
            )

            renewal = renew_contract(
                contract=contract,
                renewed_by=request.user,
                new_start_date=serializer.validated_data[
                    "new_start_date"
                ],
                new_end_date=serializer.validated_data.get(
                    "new_end_date"
                ),
                new_salary=serializer.validated_data[
                    "new_salary"
                ],
                reason=serializer.validated_data.get(
                    "reason",
                    "",
                ),
                request=request,
            )

            return Response(
                {
                    "message": "Contract renewed successfully.",
                    "renewal": ContractRenewalSerializer(
                        renewal
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    request=ContractTerminateActionSerializer,
    responses={200: ContractTerminationSerializer},
    tags=["Contracts"],
)
class TerminateContractView(APIView):
    permission_classes = [
        RequiredPermission("contracts.terminate")
    ]

    def post(self, request, contract_id):
        serializer = ContractTerminateActionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            contract = check_related_employee_permission(
                user=request.user,
                queryset=EmploymentContract.objects.select_related(
                    "employee",
                ),
                employee_field="employee",
                object_id=contract_id,
                permission_codename="contracts.terminate",
            )

            termination = terminate_contract(
                contract=contract,
                terminated_by=request.user,
                termination_type=serializer.validated_data[
                    "termination_type"
                ],
                termination_date=serializer.validated_data[
                    "termination_date"
                ],
                reason=serializer.validated_data["reason"],
                notice_period_days=serializer.validated_data[
                    "notice_period_days"
                ],
                final_settlement_required=(
                    serializer.validated_data[
                        "final_settlement_required"
                    ]
                ),
                request=request,
            )

            return Response(
                {
                    "message": (
                        "Contract terminated successfully."
                    ),
                    "termination": (
                        ContractTerminationSerializer(
                            termination
                        ).data
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
@extend_schema(
    responses={200: EmploymentContractSerializer(many=True)},
    tags=["Contracts"],
)
class EmployeeContractsView(APIView):
    permission_classes = [
        RequiredPermission("contracts.view")
    ]

    def get(self, request, employee_id):
        queryset = EmploymentContract.objects.filter(
            employee_id=employee_id,
        ).select_related(
            "employee",
            "employee__branch",
            "employee__department",
            "employee__designation",
            "created_by",
            "approved_by",
        ).order_by(
            "-start_date",
            "-created_at",
        )

        queryset = scope_related_employee_queryset(
            user=request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="contracts.view",
        )

        serializer = EmploymentContractSerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )        
