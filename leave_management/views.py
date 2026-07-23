from rest_framework import filters, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from employees.models import Employee
from accounts.permissions import RequiredPermission
from accounts.scopes import scope_related_employee_queryset
from accounts.object_permissions import (
    check_related_employee_permission,
)
from accounts.services import user_has_permission
from audit.mixins import AuditViewSetMixin
from .models import (
    LeaveType,
    LeaveBalance,
    LeaveRequest,
    LeaveApproval,
    LeaveAttachment,
    PublicHoliday,
)
from .serializers import (
    LeaveTypeSerializer,
    LeaveBalanceSerializer,
    LeaveRequestSerializer,
    LeaveApprovalSerializer,
    LeaveAttachmentSerializer,
    PublicHolidaySerializer,
    CreateLeaveRequestSerializer,
    LeaveApprovalActionSerializer,
    LeaveRejectSerializer,
)
from .services import (
    create_leave_request,
    manager_approve_leave,
    hr_approve_leave,
    reject_leave,
)


@extend_schema_view(
    list=extend_schema(tags=["Leave Management"]),
    retrieve=extend_schema(tags=["Leave Management"]),
    create=extend_schema(tags=["Leave Management"]),
    update=extend_schema(tags=["Leave Management"]),
    partial_update=extend_schema(tags=["Leave Management"]),
    destroy=extend_schema(tags=["Leave Management"]),
)
class LeaveTypeViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "LEAVE"

    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["Leave Management"]),
    retrieve=extend_schema(tags=["Leave Management"]),
    create=extend_schema(tags=["Leave Management"]),
    update=extend_schema(tags=["Leave Management"]),
    partial_update=extend_schema(tags=["Leave Management"]),
    destroy=extend_schema(tags=["Leave Management"]),
)
class LeaveBalanceViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "LEAVE"

    serializer_class = LeaveBalanceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            codename = "leave.view"
        else:
            codename = "leave.approve"

        return [RequiredPermission(codename)()]

    def get_queryset(self):
        queryset = LeaveBalance.objects.select_related(
            "employee",
            "leave_type",
        ).order_by(
            "employee__employee_number",
            "year",
        )

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="leave.view",
        )
class LeaveRequestViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "LEAVE"

    serializer_class = LeaveRequestSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "leave_type__name",
        "reason",
    ]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    filterset_fields = [
        "employee",
        "leave_type",
        "status",
        "start_date",
        "end_date",
    ]

    def get_permissions(self):
        permission_map = {
            "list": "leave.view",
            "retrieve": "leave.view",
            "create": "leave.request",
            "update": "leave.approve",
            "partial_update": "leave.approve",
            "destroy": "leave.approve",
        }

        codename = permission_map.get(
            self.action,
            "leave.view",
        )

        return [RequiredPermission(codename)()]

    def get_queryset(self):
        queryset = LeaveRequest.objects.select_related(
            "employee",
            "employee__branch",
            "employee__department",
            "leave_type",
            "requested_by",
            "manager_approved_by",
            "hr_approved_by",
        ).order_by("-created_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="leave.view",
        )

    def get_object(self):
        return check_related_employee_permission(
            user=self.request.user,
            queryset=LeaveRequest.objects.select_related(
                "employee",
                "leave_type",
            ),
            employee_field="employee",
            object_id=self.kwargs["pk"],
            permission_codename="leave.view",
        )


class LeaveApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeaveApprovalSerializer
    permission_classes = [
        RequiredPermission("leave.view")
    ]

    def get_queryset(self):
        queryset = LeaveApproval.objects.select_related(
            "leave_request",
            "leave_request__employee",
            "approver",
        ).order_by("-created_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="leave_request__employee",
            permission_codename="leave.view",
        )


class LeaveAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveAttachmentSerializer
    permission_classes = [
        RequiredPermission("leave.view")
    ]

    def get_queryset(self):
        queryset = LeaveAttachment.objects.select_related(
            "leave_request",
            "leave_request__employee",
        ).order_by("-uploaded_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="leave_request__employee",
            permission_codename="leave.view",
        )


@extend_schema_view(
    list=extend_schema(tags=["Leave Management"]),
    retrieve=extend_schema(tags=["Leave Management"]),
    create=extend_schema(tags=["Leave Management"]),
    update=extend_schema(tags=["Leave Management"]),
    partial_update=extend_schema(tags=["Leave Management"]),
    destroy=extend_schema(tags=["Leave Management"]),
)
class PublicHolidayViewSet(viewsets.ModelViewSet):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    permission_classes = [permissions.IsAuthenticated]

class CreateLeaveRequestView(APIView):
    permission_classes = [
        RequiredPermission("leave.request")
    ]

    @extend_schema(
        tags=["Leave Management"],
        request=CreateLeaveRequestSerializer,
        responses={201: LeaveRequestSerializer},
    )
    def post(self, request):
        serializer = CreateLeaveRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=serializer.validated_data["employee_id"])
            request_employee = getattr(
                request.user,
                "employee_profile",
                None,
            )

            can_manage_leave = user_has_permission(
                request.user,
                "leave.approve",
            )

            if (
                not can_manage_leave
                and (
                    not request_employee
                    or request_employee.id != employee.id
                )
            ):
                return Response(
                    {
                        "message": (
                            "You can only create leave requests "
                            "for your own employee profile."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            leave_type = LeaveType.objects.get(id=serializer.validated_data["leave_type_id"])

            leave_request = create_leave_request(
                employee=employee,
                leave_type=leave_type,
                start_date=serializer.validated_data["start_date"],
                end_date=serializer.validated_data["end_date"],
                reason=serializer.validated_data.get("reason", ""),
                requested_by=request.user,
                request=request,
            )

            return Response(
                {
                    "message": "Leave request created successfully",
                    "leave_request": LeaveRequestSerializer(leave_request).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except (Employee.DoesNotExist, LeaveType.DoesNotExist):
            return Response(
                {"message": "Employee or leave type not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ManagerApproveLeaveView(APIView):
    permission_classes = [
        RequiredPermission("leave.approve")
    ]

    @extend_schema(
        tags=["Leave Management"],
        request=LeaveApprovalActionSerializer,
        responses={200: LeaveRequestSerializer},
    )
    def post(self, request, leave_request_id):
        serializer = LeaveApprovalActionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            request_employee = getattr(
                request.user,
                "employee_profile",
                None,
            )

            if (
                request_employee
                and leave_request.employee.manager_id
                and leave_request.employee.manager_id
                != request_employee.id
                and not request.user.is_superuser
            ):
                return Response(
                    {
                        "message": (
                            "You are not the assigned manager "
                            "for this employee."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            updated_request = manager_approve_leave(
                leave_request=leave_request,
                approver=request.user,
                comment=serializer.validated_data.get("comment", ""),
                request=request,
            )

            return Response(
                {
                    "message": "Leave request approved by manager",
                    "leave_request": LeaveRequestSerializer(updated_request).data,
                },
                status=status.HTTP_200_OK,
            )

        except LeaveRequest.DoesNotExist:
            return Response(
                {"message": "Leave request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class HRApproveLeaveView(APIView):
    permission_classes = [
        RequiredPermission("leave.approve")
    ]

    @extend_schema(
        tags=["Leave Management"],
        request=LeaveApprovalActionSerializer,
        responses={200: LeaveRequestSerializer},
    )
    def post(self, request, leave_request_id):
        serializer = LeaveApprovalActionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            updated_request = hr_approve_leave(
                leave_request=leave_request,
                approver=request.user,
                comment=serializer.validated_data.get("comment", ""),
                request=request,
            )

            return Response(
                {
                    "message": "Leave request approved by HR",
                    "leave_request": LeaveRequestSerializer(updated_request).data,
                },
                status=status.HTTP_200_OK,
            )

        except LeaveRequest.DoesNotExist:
            return Response(
                {"message": "Leave request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RejectLeaveView(APIView):
    permission_classes = [
        RequiredPermission("leave.approve")
    ]

    @extend_schema(
        tags=["Leave Management"],
        request=LeaveRejectSerializer,
        responses={200: LeaveRequestSerializer},
    )
    def post(self, request, leave_request_id):
        serializer = LeaveRejectSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            updated_request = reject_leave(
                leave_request=leave_request,
                approver=request.user,
                reason=serializer.validated_data["reason"],
                request=request,
            )

            return Response(
                {
                    "message": "Leave request rejected",
                    "leave_request": LeaveRequestSerializer(updated_request).data,
                },
                status=status.HTTP_200_OK,
            )

        except LeaveRequest.DoesNotExist:
            return Response(
                {"message": "Leave request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )    
