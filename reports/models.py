from django.conf import settings
from django.db import models


class ReportTemplate(models.Model):
    REPORT_TYPES = [
        ("EMPLOYEE", "Employee"),
        ("ATTENDANCE", "Attendance"),
        ("LEAVE", "Leave"),
        ("PAYROLL", "Payroll"),
        ("PERFORMANCE", "Performance"),
        ("TRAINING", "Training"),
        ("CONTRACT", "Contract"),
        ("BENEFIT", "Benefit"),
        ("EXECUTIVE", "Executive Dashboard"),
    ]

    EXPORT_FORMATS = [
        ("JSON", "JSON"),
        ("PDF", "PDF"),
        ("EXCEL", "Excel"),
        ("CSV", "CSV"),
    ]

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPES,
    )

    description = models.TextField(blank=True)

    default_export_format = models.CharField(
        max_length=20,
        choices=EXPORT_FORMATS,
        default="PDF",
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_report_templates",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReportExecution(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    EXPORT_FORMATS = ReportTemplate.EXPORT_FORMATS

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="executions",
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_requests",
    )

    export_format = models.CharField(
        max_length=20,
        choices=EXPORT_FORMATS,
    )

    filters = models.JSONField(
        default=dict,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    generated_file = models.FileField(
        upload_to="reports/",
        null=True,
        blank=True,
    )

    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.name} ({self.status})"


class SavedReport(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_reports",
    )

    name = models.CharField(max_length=150)

    report_type = models.CharField(
        max_length=30,
        choices=ReportTemplate.REPORT_TYPES,
    )

    filters = models.JSONField(default=dict)

    export_format = models.CharField(
        max_length=20,
        choices=ReportTemplate.EXPORT_FORMATS,
        default="PDF",
    )

    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name