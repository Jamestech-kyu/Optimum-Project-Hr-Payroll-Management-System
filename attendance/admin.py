from django.contrib import admin

from .models import (
    WorkLocation,
    Shift,
    EmployeeAttendanceAssignment,
    AttendanceRecord,
    AttendanceLocationLog,
    AttendanceCorrectionRequest,
)


@admin.register(WorkLocation)
class WorkLocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "branch",
        "latitude",
        "longitude",
        "radius_meters",
        "is_active",
    )
    search_fields = ("name", "branch__name")
    list_filter = ("branch", "is_active")


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_time",
        "end_time",
        "grace_period_minutes",
        "is_active",
    )
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(EmployeeAttendanceAssignment)
class EmployeeAttendanceAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "work_location",
        "shift",
        "effective_from",
        "effective_to",
        "is_active",
    )
    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "work_location__name",
        "shift__name",
    )
    list_filter = (
        "work_location__branch",
        "work_location",
        "shift",
        "is_active",
    )


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "shift",
        "work_location",
        "check_in_time",
        "check_out_time",
        "status",
        "total_hours",
        "overtime_hours",
    )
    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
    )
    list_filter = (
        "status",
        "date",
        "work_location",
        "shift",
    )


@admin.register(AttendanceLocationLog)
class AttendanceLocationLogAdmin(admin.ModelAdmin):
    list_display = (
        "attendance",
        "log_type",
        "distance_meters",
        "within_geofence",
        "ip_address",
        "captured_at",
    )
    list_filter = (
        "log_type",
        "within_geofence",
        "captured_at",
    )


@admin.register(AttendanceCorrectionRequest)
class AttendanceCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = (
        "attendance",
        "requested_by",
        "status",
        "approved_by",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "attendance__employee__employee_number",
        "reason",
    )