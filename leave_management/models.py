from django.db import models
from django.conf import settings
from employees.models import Employee


class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    max_days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_attachment = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances",
    )

    year = models.PositiveIntegerField()
    allocated_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    remaining_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ("employee", "leave_type", "year")

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} - {self.year}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING_MANAGER", "Pending Manager Approval"),
        ("PENDING_HR", "Pending HR Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="leave_requests",
    )

    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING_MANAGER",
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leave_requests_created",
    )

    manager_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leave_requests_manager_approved",
    )

    hr_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leave_requests_hr_approved",
    )

    manager_approved_at = models.DateTimeField(null=True, blank=True)
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["employee", "status"],
                name="leave_emp_status_idx",
            ),
            models.Index(
                fields=["status", "start_date"],
                name="leave_status_start_idx",
            ),
            models.Index(
                fields=["start_date", "end_date"],
                name="leave_date_range_idx",
            ),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name}"


class LeaveApproval(models.Model):
    APPROVAL_LEVEL_CHOICES = [
        ("MANAGER", "Manager"),
        ("HR", "HR"),
    ]

    ACTION_CHOICES = [
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name="approvals",
    )

    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="leave_approvals",
    )

    approval_level = models.CharField(max_length=20, choices=APPROVAL_LEVEL_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leave_request} - {self.approval_level}"


class LeaveAttachment(models.Model):
    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(upload_to="leave/attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment - {self.leave_request}"


class PublicHoliday(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField(unique=True)
    is_recurring = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.date}"
