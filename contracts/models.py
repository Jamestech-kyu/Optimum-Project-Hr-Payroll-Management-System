from django.conf import settings
from django.db import models

from employees.models import Employee


class EmploymentContract(models.Model):
    CONTRACT_TYPE_CHOICES = [
        ("PERMANENT", "Permanent"),
        ("FIXED_TERM", "Fixed Term"),
        ("PROBATION", "Probation"),
        ("INTERNSHIP", "Internship"),
        ("CONSULTANCY", "Consultancy"),
        ("CASUAL", "Casual"),
    ]

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("ACTIVE", "Active"),
        ("EXPIRED", "Expired"),
        ("TERMINATED", "Terminated"),
        ("RENEWED", "Renewed"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="contracts",
    )

    contract_number = models.CharField(
        max_length=100,
        unique=True,
    )

    contract_type = models.CharField(
        max_length=30,
        choices=CONTRACT_TYPE_CHOICES,
    )

    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
    )

    probation_end_date = models.DateField(
        null=True,
        blank=True,
    )

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    terms = models.TextField(blank=True)

    document = models.FileField(
        upload_to="contracts/documents/",
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts_created",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts_approved",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return (
            f"{self.contract_number} - "
            f"{self.employee.full_name}"
        )


class ContractRenewal(models.Model):
    contract = models.ForeignKey(
        EmploymentContract,
        on_delete=models.CASCADE,
        related_name="renewals",
    )

    previous_end_date = models.DateField(
        null=True,
        blank=True,
    )

    new_start_date = models.DateField()
    new_end_date = models.DateField(
        null=True,
        blank=True,
    )

    previous_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    new_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    reason = models.TextField(blank=True)

    renewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="contract_renewals",
    )

    renewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-renewed_at"]

    def __str__(self):
        return f"Renewal - {self.contract.contract_number}"


class ContractTermination(models.Model):
    TERMINATION_TYPE_CHOICES = [
        ("RESIGNATION", "Resignation"),
        ("DISMISSAL", "Dismissal"),
        ("REDUNDANCY", "Redundancy"),
        ("RETIREMENT", "Retirement"),
        ("END_OF_CONTRACT", "End of Contract"),
        ("MUTUAL_AGREEMENT", "Mutual Agreement"),
        ("OTHER", "Other"),
    ]

    contract = models.OneToOneField(
        EmploymentContract,
        on_delete=models.CASCADE,
        related_name="termination",
    )

    termination_type = models.CharField(
        max_length=30,
        choices=TERMINATION_TYPE_CHOICES,
    )

    termination_date = models.DateField()
    reason = models.TextField()

    notice_period_days = models.PositiveIntegerField(default=0)

    final_settlement_required = models.BooleanField(default=True)

    terminated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="contracts_terminated",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Termination - {self.contract.contract_number}"