from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from employees.models import Employee
from .models import (
    WorkLocation,
    Shift,
    AttendanceRecord,
    AttendanceLocationLog,
    AttendanceCorrectionRequest,
)
from .serializers import (
    WorkLocationSerializer,
    ShiftSerializer,
    AttendanceRecordSerializer,
    AttendanceLocationLogSerializer,
    AttendanceCorrectionRequestSerializer,
    CheckInSerializer,
    CheckOutSerializer,
)
from .services import is_within_geofence


class WorkLocationViewSet(viewsets.ModelViewSet):
    queryset = WorkLocation.objects.all()
    serializer_class = WorkLocationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttendanceLocationLogViewSet(viewsets.ModelViewSet):
    queryset = AttendanceLocationLog.objects.all()
    serializer_class = AttendanceLocationLogSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttendanceCorrectionRequestViewSet(viewsets.ModelViewSet):
    queryset = AttendanceCorrectionRequest.objects.all()
    serializer_class = AttendanceCorrectionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]


class CheckInView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        employee_id = serializer.validated_data["employee_id"]
        work_location_id = serializer.validated_data["work_location_id"]
        shift_id = serializer.validated_data.get("shift_id")
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]

        try:
            employee = Employee.objects.get(id=employee_id)
            work_location = WorkLocation.objects.get(id=work_location_id)
        except (Employee.DoesNotExist, WorkLocation.DoesNotExist):
            return Response(
                {"message": "Employee or work location not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        shift = None
        if shift_id:
            shift = Shift.objects.filter(id=shift_id).first()

        today = timezone.localdate()

        if AttendanceRecord.objects.filter(employee=employee, date=today).exists():
            return Response(
                {"message": "Employee has already checked in today"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        within_geofence = is_within_geofence(latitude, longitude, work_location)

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
            status="PRESENT",
        )

        AttendanceLocationLog.objects.create(
            attendance=attendance,
            log_type="CHECK_IN",
            latitude=latitude,
            longitude=longitude,
            within_geofence=within_geofence,
        )

        return Response(
            {
                "message": "Check-in successful",
                "attendance": AttendanceRecordSerializer(attendance).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CheckOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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

        if attendance.check_out_time:
            return Response(
                {"message": "Employee has already checked out today"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        within_geofence = False

        if attendance.work_location:
            within_geofence = is_within_geofence(
                latitude,
                longitude,
                attendance.work_location,
            )

        if not within_geofence:
            return Response(
                {"message": "You are outside the allowed geofence location"},
                status=status.HTTP_403_FORBIDDEN,
            )

        attendance.check_out_time = timezone.now()
        attendance.check_out_latitude = latitude
        attendance.check_out_longitude = longitude
        attendance.check_out_within_geofence = within_geofence

        duration = attendance.check_out_time - attendance.check_in_time
        attendance.total_hours = round(duration.total_seconds() / 3600, 2)

        attendance.save()

        AttendanceLocationLog.objects.create(
            attendance=attendance,
            log_type="CHECK_OUT",
            latitude=latitude,
            longitude=longitude,
            within_geofence=within_geofence,
        )

        return Response(
            {
                "message": "Check-out successful",
                "attendance": AttendanceRecordSerializer(attendance).data,
            },
            status=status.HTTP_200_OK,
        )