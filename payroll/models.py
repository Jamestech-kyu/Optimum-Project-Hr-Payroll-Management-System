from django.db import models
from django.conf import settings
from employees.models import Employee

class PayComponent(models.Model):
    COMPONENT_TYPE_CHOICES = [
        ("EARNING", "Earning"),
        ("DEDUCTION", "Deduction"),
        ("TAX", "Tax"),
    ]

    CALCULATION_TYPE_CHOICES = [
        ("FIXED", "Fixed Amount"),
        ("PERCENTAGE", "Percentage"),
    ]

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, unique=True)

    component_type = models.CharField(
        max_length=20,
        choices=COMPONENT_TYPE_CHOICES,
    )

    calculation_type = models.CharField(
        max_length=20,
        choices=CALCULATION_TYPE_CHOICES,
        default="FIXED",
    )

    default_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    percentage_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    is_taxable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.component_type})"
class TaxBand(models.Model):
    name = models.CharField(max_length=100, default="PAYE")
    min_income = models.DecimalField(max_digits=12, decimal_places=2)
    max_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["min_income"]

    def __str__(self):
        return f"{self.name}: {self.min_income} - {self.max_income or 'Above'} @ {self.rate}%"


class StatutoryRate(models.Model):
    STATUTORY_TYPE_CHOICES = [
        ("NSSF", "NSSF"),
        ("SHIF", "SHIF"),
        ("HOUSING_LEVY", "Housing Levy"),
        ("PENSION", "Pension"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    statutory_type = models.CharField(max_length=30, choices=STATUTORY_TYPE_CHOICES)
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    is_percentage = models.BooleanField(default=True)
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.rate}{'%' if self.is_percentage else ''}"


class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, blank=True)
    is_base_currency = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class ExchangeRate(models.Model):
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="exchange_rates_from",
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="exchange_rates_to",
    )
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("from_currency", "to_currency", "effective_date")

    def __str__(self):
        return f"{self.from_currency} to {self.to_currency} = {self.rate}"


class PayrollPolicy(models.Model):
    name = models.CharField(max_length=150, unique=True)
    working_days_per_month = models.PositiveIntegerField(default=22)
    working_hours_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    overtime_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.5)
    weekend_overtime_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    payroll_cutoff_day = models.PositiveIntegerField(default=25)
    payslip_generation_day = models.PositiveIntegerField(default=28)

    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_policies",
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name    


class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING_APPROVAL", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("FINALIZED", "Finalized"),
        ("CANCELLED", "Cancelled"),
    ]

    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="DRAFT")

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_runs_processed",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_runs_approved",
    )

    processed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("month", "year")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["year", "month", "status"],
                name="payrun_year_month_status_idx",
            ),
            models.Index(
                fields=["created_at"],
                name="payrun_created_idx",
            ),
        ]

    def __str__(self):
        return f"Payroll {self.month}/{self.year}"
    
class EmployeePayComponent(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="pay_components",
    )

    component = models.ForeignKey(
        PayComponent,
        on_delete=models.CASCADE,
        related_name="employee_components",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("employee", "component")

    def __str__(self):
        return f"{self.employee.full_name} - {self.component.name}"   


class Payslip(models.Model):
    payroll_run = models.ForeignKey(
        PayrollRun,
        on_delete=models.CASCADE,
        related_name="payslips",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payslips",
    )

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("payroll_run", "employee")
        ordering = ["-generated_at"]
        indexes = [
            models.Index(
                fields=["employee", "payroll_run"],
                name="payslip_emp_run_idx",
            ),
            models.Index(
                fields=["payroll_run"],
                name="payslip_run_idx",
            ),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_run}"


class PayrollDeduction(models.Model):
    payslip = models.ForeignKey(
        Payslip,
        on_delete=models.CASCADE,
        related_name="deductions",
    )

    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"


class PayrollAllowance(models.Model):
    payslip = models.ForeignKey(
        Payslip,
        on_delete=models.CASCADE,
        related_name="allowances",
    )

    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"


class BankPayment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
    ]

    payroll_run = models.ForeignKey(
        PayrollRun,
        on_delete=models.CASCADE,
        related_name="bank_payments",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="bank_payments",
    )

    bank_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=150)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.amount}"
