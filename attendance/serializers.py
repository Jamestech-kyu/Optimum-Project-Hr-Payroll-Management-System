from rest_framework import serializers
from .models import (
    WorkLocation,
    Shift,
    EmployeeAttendanceAssignment,
    AttendanceRecord,
    AttendanceLocationLog,
    AttendanceCorrectionRequest,
)


class WorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocation
        fields = "__all__"


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = "__all__"


class EmployeeAttendanceAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendanceAssignment
        fields = "__all__"


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = "__all__"


class AttendanceLocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceLocationLog
        fields = "__all__"


class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceCorrectionRequest
        fields = "__all__"


class CheckInSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
    )


class CheckOutSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
