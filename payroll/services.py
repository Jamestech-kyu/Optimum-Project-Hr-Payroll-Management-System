from decimal import Decimal
from calendar import monthrange
from datetime import date

from django.db import transaction
from django.utils import timezone

from employees.models import Employee
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    PayrollRun,
    Payslip,
    PayrollAllowance,
    PayrollDeduction,
    BankPayment,
    EmployeePayComponent,
    TaxBand,
    StatutoryRate,
)

def calculate_employee_basic_salary(employee):
    return employee.basic_salary or Decimal("0.00")


def calculate_employee_allowances(employee):
    allowances = {
        "House Allowance": employee.house_allowance or Decimal("0.00"),
        "Transport Allowance": employee.transport_allowance or Decimal("0.00"),
        "Medical Allowance": employee.medical_allowance or Decimal("0.00"),
        "Other Allowance": employee.other_allowance or Decimal("0.00"),
    }

    total = sum(allowances.values(), Decimal("0.00"))

    return total, allowances


def calculate_employee_extra_components(employee):
    earnings = {}
    deductions = {}

    components = EmployeePayComponent.objects.filter(
        employee=employee,
        is_active=True,
        component__is_active=True,
    )

    for item in components:
        component = item.component
        # A percentage component is a percentage of the employee's basic
        # salary.  An employee-specific amount deliberately takes precedence;
        # it lets payroll override the configured default for one employee.
        if component.calculation_type == "PERCENTAGE":
            rate = item.amount or component.percentage_rate or Decimal("0.00")
            amount = calculate_employee_basic_salary(employee) * (
                rate / Decimal("100.00")
            )
        else:
            amount = item.amount or component.default_amount or Decimal("0.00")

        amount = amount.quantize(Decimal("0.01"))

        if component.component_type == "EARNING":
            earnings[component.name] = amount

        elif component.component_type in ["DEDUCTION", "TAX"]:
            deductions[component.name] = amount

    return earnings, deductions


def calculate_gross_pay(employee):
    basic_salary = calculate_employee_basic_salary(employee)
    total_allowances, allowances = calculate_employee_allowances(employee)
    extra_earnings, extra_deductions = calculate_employee_extra_components(employee)

    gross_pay = basic_salary + total_allowances + sum(
        extra_earnings.values(),
        Decimal("0.00"),
    )

    return {
        "basic_salary": basic_salary,
        "allowances": allowances,
        "extra_earnings": extra_earnings,
        "extra_deductions": extra_deductions,
        "gross_pay": gross_pay,
    }


def calculate_paye(taxable_income, effective_date=None):
    paye = Decimal("0.00")

    effective_date = effective_date or timezone.localdate()
    tax_bands = TaxBand.objects.filter(
        name="PAYE",
        is_active=True,
        effective_from__lte=effective_date,
    ).order_by("min_income")

    for band in tax_bands:
        min_income = band.min_income
        max_income = band.max_income
        rate = band.rate / Decimal("100.00")

        if taxable_income <= min_income:
            continue

        upper_limit = max_income if max_income else taxable_income
        taxable_amount = min(taxable_income, upper_limit) - min_income

        if taxable_amount > 0:
            paye += taxable_amount * rate

    return paye.quantize(Decimal("0.01"))


def calculate_statutory_deductions(gross_pay, effective_date=None):
    deductions = {}

    effective_date = effective_date or timezone.localdate()
    rates = StatutoryRate.objects.filter(
        is_active=True,
        effective_from__lte=effective_date,
    )

    for rate in rates:
        if rate.is_percentage:
            amount = gross_pay * (rate.rate / Decimal("100.00"))
        else:
            amount = rate.rate

        deductions[rate.name] = amount.quantize(Decimal("0.01"))

    return deductions


def calculate_employee_payroll(employee, effective_date=None):
    gross_data = calculate_gross_pay(employee)

    gross_pay = gross_data["gross_pay"]
    taxable_income = gross_pay

    paye = calculate_paye(taxable_income, effective_date=effective_date)

    statutory_deductions = calculate_statutory_deductions(
        gross_pay,
        effective_date=effective_date,
    )
    extra_deductions = gross_data["extra_deductions"]

    total_deductions = (
        paye
        + sum(statutory_deductions.values(), Decimal("0.00"))
        + sum(extra_deductions.values(), Decimal("0.00"))
    )

    net_pay = gross_pay - total_deductions

    return {
        "basic_salary": gross_data["basic_salary"],
        "allowances": gross_data["allowances"],
        "extra_earnings": gross_data["extra_earnings"],
        "gross_pay": gross_pay.quantize(Decimal("0.01")),
        "paye": paye,
        "statutory_deductions": statutory_deductions,
        "extra_deductions": extra_deductions,
        "total_deductions": total_deductions.quantize(Decimal("0.01")),
        "net_pay": net_pay.quantize(Decimal("0.01")),
    }


def generate_payslip(payroll_run, employee):
    period_end = date(
        payroll_run.year,
        payroll_run.month,
        monthrange(payroll_run.year, payroll_run.month)[1],
    )
    payroll_data = calculate_employee_payroll(
        employee,
        effective_date=period_end,
    )

    payslip, created = Payslip.objects.update_or_create(
        payroll_run=payroll_run,
        employee=employee,
        defaults={
            "basic_salary": payroll_data["basic_salary"],
            "total_allowances": sum(
                payroll_data["allowances"].values(),
                Decimal("0.00"),
            )
            + sum(
                payroll_data["extra_earnings"].values(),
                Decimal("0.00"),
            ),
            "gross_pay": payroll_data["gross_pay"],
            "tax_amount": payroll_data["paye"],
            "total_deductions": payroll_data["total_deductions"],
            "net_pay": payroll_data["net_pay"],
        },
    )

    payslip.allowances.all().delete()
    payslip.deductions.all().delete()

    for name, amount in payroll_data["allowances"].items():
        PayrollAllowance.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    for name, amount in payroll_data["extra_earnings"].items():
        PayrollAllowance.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    PayrollDeduction.objects.create(
        payslip=payslip,
        name="PAYE",
        amount=payroll_data["paye"],
    )

    for name, amount in payroll_data["statutory_deductions"].items():
        PayrollDeduction.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    for name, amount in payroll_data["extra_deductions"].items():
        PayrollDeduction.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    primary_account = employee.bank_accounts.filter(is_primary=True).first()
    if primary_account is None:
        primary_account = employee.bank_accounts.first()

    BankPayment.objects.update_or_create(
        payroll_run=payroll_run,
        employee=employee,
        defaults={
            "bank_name": (
                primary_account.bank_name if primary_account else employee.bank_name
            ),
            "account_number": (
                primary_account.account_number
                if primary_account
                else employee.bank_account_number
            ),
            "account_name": (
                primary_account.account_name
                if primary_account
                else employee.bank_account_name
            ),
            "amount": payroll_data["net_pay"],
            "status": "PENDING",
        },
    )

    return payslip


def generate_payroll_run(month, year, processed_by, request=None, employee_ids=None):
    payroll_run, created = PayrollRun.objects.get_or_create(
        month=month,
        year=year,
        defaults={
            "processed_by": processed_by,
            "processed_at": timezone.now(),
            "status": "DRAFT",
        },
    )

    if payroll_run.status != "DRAFT":
        raise ValueError(
            "Only a draft payroll can be regenerated. Create a new run or "
            "cancel the existing run before making changes."
        )

    employees = Employee.objects.filter(
        employment_status__in=["ACTIVE", "PROBATION", "ONBOARDING"]
    )
    if employee_ids:
        employees = employees.filter(id__in=employee_ids)

    if not employees.exists():
        raise ValueError("No eligible employees were found for this payroll run.")

    for employee in employees:
        generate_payslip(payroll_run, employee)

    payroll_run.processed_by = processed_by
    payroll_run.processed_at = timezone.now()
    payroll_run.save(update_fields=["processed_by", "processed_at"])

    log_activity(
        user=processed_by,
        action="CREATE",
        module="Payroll",
        description=f"Generated payroll for {month}/{year}.",
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return payroll_run
@transaction.atomic
def submit_payroll_for_approval(
    payroll_run,
    submitted_by,
    comment="",
    request=None,
):
    if payroll_run.status != "DRAFT":
        raise ValueError(
            "Only a draft payroll can be submitted for approval."
        )

    if not payroll_run.payslips.exists():
        raise ValueError(
            "Payroll cannot be submitted because it has no payslips."
        )

    payroll_run.status = "PENDING_APPROVAL"
    payroll_run.save(update_fields=["status"])

    description = (
        f"Submitted payroll {payroll_run.month}/"
        f"{payroll_run.year} for approval."
    )

    if comment:
        description += f" Comment: {comment}"

    log_activity(
        user=submitted_by,
        action="UPDATE",
        module="Payroll",
        description=description,
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return payroll_run


@transaction.atomic
def approve_payroll_run(
    payroll_run,
    approved_by,
    comment="",
    request=None,
):
    if payroll_run.status != "PENDING_APPROVAL":
        raise ValueError(
            "Only payroll pending approval can be approved."
        )
    if payroll_run.payslips.exclude(approval_status="APPROVED").exists():
        raise ValueError("All payroll items must be reviewed and approved before approving the payroll run.")

    payroll_run.status = "APPROVED"
    payroll_run.approved_by = approved_by
    payroll_run.approved_at = timezone.now()

    payroll_run.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
        ]
    )

    description = (
        f"Approved payroll {payroll_run.month}/"
        f"{payroll_run.year}."
    )

    if comment:
        description += f" Comment: {comment}"

    log_activity(
        user=approved_by,
        action="APPROVE",
        module="Payroll",
        description=description,
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return payroll_run


@transaction.atomic
def review_payslips(payroll_run, payslip_ids, action, reviewed_by, comment="", request=None):
    if payroll_run.status != "PENDING_APPROVAL":
        raise ValueError("Only payroll pending approval can have its items reviewed.")

    payslips = payroll_run.payslips.filter(id__in=set(payslip_ids))
    if payslips.count() != len(set(payslip_ids)):
        raise ValueError("One or more payroll items do not belong to this payroll run.")

    review_status = "APPROVED" if action == "APPROVE" else "REJECTED"
    payslips.update(approval_status=review_status, approval_comment=comment, reviewed_by=reviewed_by, reviewed_at=timezone.now())
    log_activity(
        user=reviewed_by,
        action="APPROVE" if action == "APPROVE" else "REJECT",
        module="Payroll",
        description=f"{review_status.title()} {payslips.count()} payroll item(s) for {payroll_run.month}/{payroll_run.year}." + (f" Comment: {comment}" if comment else ""),
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )
    return payslips


@transaction.atomic
def finalize_payroll_run(
    payroll_run,
    finalized_by,
    comment="",
    request=None,
):
    if payroll_run.status != "APPROVED":
        raise ValueError(
            "Only an approved payroll can be finalized."
        )

    # Synchronize bank payment records with the latest employee bank details
    for payment in payroll_run.bank_payments.select_related("employee"):
        employee = payment.employee
        primary_account = employee.bank_accounts.filter(is_primary=True).first()
        if primary_account is None:
            primary_account = employee.bank_accounts.first()

        payment.bank_name = (
            primary_account.bank_name if primary_account else employee.bank_name
        )
        payment.account_number = (
            primary_account.account_number
            if primary_account
            else employee.bank_account_number
        )
        payment.account_name = (
            primary_account.account_name
            if primary_account
            else employee.bank_account_name
        )

        payment.save(
            update_fields=[
                "bank_name",
                "account_number",
                "account_name",
            ]
        )

    missing_accounts = payroll_run.bank_payments.filter(
        account_number=""
    ).select_related("employee")

    if missing_accounts.exists():
        employees = ", ".join(
            payment.employee.full_name
            for payment in missing_accounts
        )

        raise ValueError(
            "Payroll cannot be finalized. Missing bank account "
            f"numbers for: {employees}"
        )

    payroll_run.status = "FINALIZED"
    payroll_run.save(update_fields=["status"])

    description = (
        f"Finalized and locked payroll "
        f"{payroll_run.month}/{payroll_run.year}."
    )

    if comment:
        description += f" Comment: {comment}"

    log_activity(
        user=finalized_by,
        action="APPROVE",
        module="Payroll",
        description=description,
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return payroll_run


@transaction.atomic
def cancel_payroll_run(
    payroll_run,
    cancelled_by,
    reason,
    request=None,
):
    if payroll_run.status == "FINALIZED":
        raise ValueError(
            "A finalized payroll cannot be cancelled."
        )

    if payroll_run.status == "CANCELLED":
        raise ValueError(
            "This payroll has already been cancelled."
        )

    payroll_run.status = "CANCELLED"
    payroll_run.save(update_fields=["status"])

    payroll_run.bank_payments.exclude(
        status="PAID"
    ).update(status="FAILED")

    log_activity(
        user=cancelled_by,
        action="UPDATE",
        module="Payroll",
        description=(
            f"Cancelled payroll {payroll_run.month}/"
            f"{payroll_run.year}. Reason: {reason}"
        ),
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return payroll_run
