from django.conf import settings
from django.db import models

from departments.models import Branch
from employees.models import Employee


class WorkLocation(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="work_locations",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=150)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["branch__name", "name"]
        unique_together = ("branch", "name")

    def __str__(self):
        if self.branch:
            return f"{self.branch.name} - {self.name}"

        return self.name


class Shift(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
class EmployeeAttendanceAssignment(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_assignment",
    )

    work_location = models.ForeignKey(
        WorkLocation,
        on_delete=models.PROTECT,
        related_name="employee_assignments",
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name="employee_assignments",
    )

    effective_from = models.DateField()
    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__employee_number"]

    def __str__(self):
        return (
            f"{self.employee.employee_number} - "
            f"{self.work_location} - {self.shift}"
        )


STATUS_CHOICES = [
    ("PRESENT", "Present"),
    ("LATE", "Late"),
    ("EARLY_LEAVE", "Early Leave"),
    ("OVERTIME", "Overtime"),
    ("ABSENT", "Absent"),
    ("ON_LEAVE", "On Leave"),
    ("HOLIDAY", "Holiday"),
    ("INCOMPLETE", "Incomplete"),
]


class AttendanceRecord(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    work_location = models.ForeignKey(
        WorkLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    date = models.DateField()

    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    check_in_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    check_in_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    check_out_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    check_out_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    check_in_within_geofence = models.BooleanField(default=False)
    check_out_within_geofence = models.BooleanField(default=False)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PRESENT",
    )

    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "date"],
                name="unique_employee_attendance_per_day",
            ),
        ]
        ordering = ["-date", "-check_in_time"]
        indexes = [
            models.Index(
                fields=["date", "status"],
                name="attendance_date_status_idx",
            ),
            models.Index(
                fields=["employee", "status"],
                name="attendance_emp_status_idx",
            ),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"


class AttendanceLocationLog(models.Model):
    LOG_TYPE_CHOICES = [
        ("CHECK_IN", "Check In"),
        ("CHECK_OUT", "Check Out"),
    ]

    attendance = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name="location_logs",
    )

    log_type = models.CharField(
        max_length=20,
        choices=LOG_TYPE_CHOICES,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    within_geofence = models.BooleanField(default=False)

    distance_meters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(blank=True)

    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self):
        return f"{self.attendance.employee.full_name} - {self.log_type}"


class AttendanceCorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    attendance = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name="correction_requests",
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="attendance_corrections_requested",
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_corrections_approved",
    )

    review_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Correction - {self.attendance.employee.full_name}"
