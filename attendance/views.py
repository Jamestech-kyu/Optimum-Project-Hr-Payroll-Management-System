from django.utils import timezone
from rest_framework import filters, status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from accounts.permissions import RequiredPermission
from accounts.object_permissions import (
    check_related_employee_permission,
)
from accounts.scopes import scope_related_employee_queryset
from accounts.services import user_has_permission


from audit.mixins import AuditViewSetMixin
from audit.utils import get_client_ip
from employees.models import Employee
from .services import (
    get_geofence_result,
    determine_attendance_status,
    calculate_checkout_summary,
)
from .models import (
    WorkLocation,
    Shift,
    EmployeeAttendanceAssignment,
    AttendanceRecord,
    AttendanceLocationLog,
    AttendanceCorrectionRequest,
)
from .serializers import (
    WorkLocationSerializer,
    ShiftSerializer,
    EmployeeAttendanceAssignmentSerializer,
    AttendanceRecordSerializer,
    AttendanceLocationLogSerializer,
    AttendanceCorrectionRequestSerializer,
    CheckInSerializer,
    CheckOutSerializer,
)


class WorkLocationViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "ATTENDANCE"

    queryset = WorkLocation.objects.all()
    serializer_class = WorkLocationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ShiftViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "ATTENDANCE"

    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmployeeAttendanceAssignmentViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "ATTENDANCE"

    queryset = EmployeeAttendanceAssignment.objects.all()
    serializer_class = EmployeeAttendanceAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttendanceRecordViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "ATTENDANCE"

    serializer_class = AttendanceRecordSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "status",
    ]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    filterset_fields = [
        "employee",
        "shift",
        "work_location",
        "status",
        "date",
    ]

    def get_permissions(self):
        permission_map = {
            "list": "attendance.view",
            "retrieve": "attendance.view",
            "create": "attendance.manage",
            "update": "attendance.manage",
            "partial_update": "attendance.manage",
            "destroy": "attendance.manage",
        }

        codename = permission_map.get(
            self.action,
            "attendance.view",
        )

        return [RequiredPermission(codename)()]

    def get_queryset(self):
        queryset = AttendanceRecord.objects.select_related(
            "employee",
            "employee__branch",
            "employee__department",
            "shift",
            "work_location",
        ).order_by("-date", "-check_in_time")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="employee",
            permission_codename="attendance.view",
        )

    def get_object(self):
        return check_related_employee_permission(
            user=self.request.user,
            queryset=AttendanceRecord.objects.select_related(
                "employee",
            ),
            employee_field="employee",
            object_id=self.kwargs["pk"],
            permission_codename="attendance.view",
        )


class AttendanceLocationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttendanceLocationLogSerializer
    permission_classes = [
        RequiredPermission("attendance.view")
    ]

    def get_queryset(self):
        queryset = AttendanceLocationLog.objects.select_related(
            "attendance",
            "attendance__employee",
        ).order_by("-captured_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="attendance__employee",
            permission_codename="attendance.view",
        )


class AttendanceCorrectionRequestViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "ATTENDANCE"

    serializer_class = AttendanceCorrectionRequestSerializer

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "create",
        ]:
            codename = "attendance.view"
        else:
            codename = "attendance.manage"

        return [RequiredPermission(codename)()]

    def get_queryset(self):
        queryset = AttendanceCorrectionRequest.objects.select_related(
            "attendance",
            "attendance__employee",
            "requested_by",
            "approved_by",
        ).order_by("-created_at")

        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=queryset,
            employee_field="attendance__employee",
            permission_codename="attendance.view",
        )

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)


class CheckInView(APIView):
    permission_classes = [
        RequiredPermission("attendance.view")
    ]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        employee_id = serializer.validated_data["employee_id"]
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        request_employee = getattr(
            request.user,
            "employee_profile",
            None,
        )

        can_manage_attendance = user_has_permission(
            request.user,
            "attendance.manage",
        )

        if (
            not can_manage_attendance
            and (
                not request_employee
                or request_employee.id != employee.id
            )
        ):
            return Response(
                {
                    "message": (
                        "You can only check in for your own "
                        "employee profile."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            assignment = EmployeeAttendanceAssignment.objects.get(
                employee_id=employee_id,
                is_active=True,
            )
        except EmployeeAttendanceAssignment.DoesNotExist:
            return Response(
                {
                    "message": "Employee has no active attendance assignment."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        work_location = assignment.work_location
        shift = assignment.shift

        today = timezone.localdate()

        if AttendanceRecord.objects.filter(employee=employee, date=today).exists():
            return Response(
                {"message": "Employee has already checked in today"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        geofence_result = get_geofence_result(
            latitude,
            longitude,
            work_location,
        )
        within_geofence = geofence_result["within_geofence"]

        if not within_geofence:
            return Response(
                {"message": "You are outside the allowed geofence location"},
                status=status.HTTP_403_FORBIDDEN,
            )

        attendance = AttendanceRecord.objects.create(
            employee=employee,
            shift=shift,
            work_location=work_location,
            date=today,
            check_in_time=timezone.now(),
            check_in_latitude=latitude,
            check_in_longitude=longitude,
            check_in_within_geofence=within_geofence,
            status=determine_attendance_status(shift),
        )

        AttendanceLocationLog.objects.create(
            attendance=attendance,
            log_type="CHECK_IN",
            latitude=latitude,
            longitude=longitude,
            within_geofence=within_geofence,
            distance_meters=geofence_result["distance_meters"],
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {
                "message": "Check-in successful",
                "attendance": AttendanceRecordSerializer(attendance).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CheckOutView(APIView):
    permission_classes = [
        RequiredPermission("attendance.view")
    ]

    def post(self, request):
        serializer = CheckOutSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        employee_id = serializer.validated_data["employee_id"]
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]

        today = timezone.localdate()

        try:
            employee = Employee.objects.get(id=employee_id)
            attendance = AttendanceRecord.objects.get(employee=employee, date=today)
        except (Employee.DoesNotExist, AttendanceRecord.DoesNotExist):
            return Response(
                {"message": "Attendance record not found for today"},
                status=status.HTTP_404_NOT_FOUND,
            )

        request_employee = getattr(
            request.user,
            "employee_profile",
            None,
        )

        can_manage_attendance = user_has_permission(
            request.user,
            "attendance.manage",
        )

        if (
            not can_manage_attendance
            and (
                not request_employee
                or request_employee.id != employee.id
            )
        ):
            return Response(
                {
                    "message": (
                        "You can only check out for your own "
                        "employee profile."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if attendance.check_out_time:
            return Response(
                {"message": "Employee has already checked out today"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        geofence_result = {
            "within_geofence": False,
            "distance_meters": None,
        }

        if attendance.work_location:
            geofence_result = get_geofence_result(
                latitude,
                longitude,
                attendance.work_location,
            )
        within_geofence = geofence_result["within_geofence"]

        if not within_geofence:
            return Response(
                {"message": "You are outside the allowed geofence location"},
                status=status.HTTP_403_FORBIDDEN,
            )

        checkout_time = timezone.now()

        summary = calculate_checkout_summary(
            attendance=attendance,
            checkout_time=checkout_time,
        )

        attendance.check_out_time = summary["checkout_time"]
        attendance.check_out_latitude = latitude
        attendance.check_out_longitude = longitude
        attendance.check_out_within_geofence = within_geofence
        attendance.total_hours = summary["total_hours"]
        attendance.overtime_hours = summary["overtime_hours"]
        attendance.status = summary["status"]

        attendance.save(
            update_fields=[
                "check_out_time",
                "check_out_latitude",
                "check_out_longitude",
                "check_out_within_geofence",
                "total_hours",
                "overtime_hours",
                "status",
                "updated_at",
            ]
        )

        AttendanceLocationLog.objects.create(
            attendance=attendance,
            log_type="CHECK_OUT",
            latitude=latitude,
            longitude=longitude,
            within_geofence=within_geofence,
            distance_meters=geofence_result["distance_meters"],
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {
                "message": "Check-out successful",
                "attendance": AttendanceRecordSerializer(attendance).data,
            },
            status=status.HTTP_200_OK,
        )
