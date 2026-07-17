from django.conf import settings
from django.db import models

from employees.models import Employee


class BenefitPlan(models.Model):
    BENEFIT_TYPE_CHOICES = [
        ("MEDICAL", "Medical Insurance"),
        ("PENSION", "Pension"),
        ("LIFE_INSURANCE", "Life Insurance"),
        ("TRANSPORT", "Transport"),
        ("MEAL", "Meal"),
        ("AIRTIME", "Airtime"),
        ("GYM", "Gym"),
        ("SACCO", "SACCO"),
        ("WELFARE", "Welfare"),
        ("OTHER", "Other"),
    ]

    CONTRIBUTION_TYPE_CHOICES = [
        ("FIXED", "Fixed Amount"),
        ("PERCENTAGE", "Percentage"),
    ]

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    code = models.CharField(
        max_length=50,
        unique=True,
    )

    benefit_type = models.CharField(
        max_length=30,
        choices=BENEFIT_TYPE_CHOICES,
    )

    description = models.TextField(blank=True)

    contribution_type = models.CharField(
        max_length=20,
        choices=CONTRIBUTION_TYPE_CHOICES,
        default="FIXED",
    )

    employee_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    employer_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    requires_approval = models.BooleanField(default=False)

    is_taxable = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class EnrollmentWindow(models.Model):
    title = models.CharField(max_length=150)

    start_date = models.DateField()

    end_date = models.DateField()

    is_open = models.BooleanField(default=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.title


class EmployeeBenefit(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("TERMINATED", "Terminated"),
        ("REJECTED", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="benefit_enrollments",
    )

    benefit_plan = models.ForeignKey(
        BenefitPlan,
        on_delete=models.PROTECT,
        related_name="employee_enrollments",
    )

    enrollment_window = models.ForeignKey(
        EnrollmentWindow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
    )

    enrollment_date = models.DateField()

    effective_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    employee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    employer_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    remarks = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="benefit_enrollments_created",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="benefit_enrollments_approved",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee",
                    "benefit_plan",
                ],
                condition=models.Q(
                    status__in=[
                        "PENDING",
                        "ACTIVE",
                        "SUSPENDED",
                    ]
                ),
                name="unique_open_employee_benefit",
            ),
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.employee.employee_number} - "
            f"{self.benefit_plan.name}"
        )


class BenefitContributionHistory(models.Model):
    employee_benefit = models.ForeignKey(
        EmployeeBenefit,
        on_delete=models.CASCADE,
        related_name="contribution_history",
    )

    payroll_month = models.PositiveIntegerField()

    payroll_year = models.PositiveIntegerField()

    employee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    employer_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee_benefit",
                    "payroll_month",
                    "payroll_year",
                ],
                name="unique_benefit_contribution_period",
            ),
        ]

        ordering = [
            "-payroll_year",
            "-payroll_month",
        ]

    def __str__(self):
        return (
            f"{self.employee_benefit} - "
            f"{self.payroll_month}/{self.payroll_year}"
        )