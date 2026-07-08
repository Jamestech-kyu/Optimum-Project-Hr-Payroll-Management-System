from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view
from employees.models import Employee

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
class LeaveTypeViewSet(viewsets.ModelViewSet):
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
class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["Leave Management"]),
    retrieve=extend_schema(tags=["Leave Management"]),
    create=extend_schema(tags=["Leave Management"]),
    update=extend_schema(tags=["Leave Management"]),
    partial_update=extend_schema(tags=["Leave Management"]),
    destroy=extend_schema(tags=["Leave Management"]),
)
class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["Leave Management"]),
    retrieve=extend_schema(tags=["Leave Management"]),
    create=extend_schema(tags=["Leave Management"]),
    update=extend_schema(tags=["Leave Management"]),
    partial_update=extend_schema(tags=["Leave Management"]),
    destroy=extend_schema(tags=["Leave Management"]),
)
class LeaveApprovalViewSet(viewsets.ModelViewSet):
    queryset = LeaveApproval.objects.all()
    serializer_class = LeaveApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["Leave Management"]),
    retrieve=extend_schema(tags=["Leave Management"]),
    create=extend_schema(tags=["Leave Management"]),
    update=extend_schema(tags=["Leave Management"]),
    partial_update=extend_schema(tags=["Leave Management"]),
    destroy=extend_schema(tags=["Leave Management"]),
)
class LeaveAttachmentViewSet(viewsets.ModelViewSet):
    queryset = LeaveAttachment.objects.all()
    serializer_class = LeaveAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]


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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
