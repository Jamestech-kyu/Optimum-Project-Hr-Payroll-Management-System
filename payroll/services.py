import logging
from decimal import Decimal
from calendar import monthrange
from datetime import date

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from employees.models import Employee
from audit.services import log_activity
from audit.utils import get_client_ip

from .calculators import (
    calculate_employee_allowances,
    calculate_employee_basic_salary,
    calculate_employee_extra_components,
    calculate_employee_extra_deductions,
    calculate_employee_extra_earnings,
    calculate_employee_payroll,
    calculate_gross_pay,
    calculate_paye,
    calculate_statutory_deductions,
)
from .generators import generate_payslip
from .models import PayrollRun

logger = logging.getLogger(__name__)


def generate_payroll_run(month, year, processed_by, request=None):
    payroll_run, created = PayrollRun.objects.get_or_create(
        month=month,
        year=year,
        defaults={
            "processed_by": processed_by,
            "status": "DRAFT",
        },
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
    log_activity(
        user=processed_by,
        action="CREATE",
        module="Payroll",
        description=f"Queued payroll generation for {month}/{year}.",
        object_id=payroll_run.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return payroll_run


class PayrollProcessor:
    ALLOWED_STATUSES = {
        "DRAFT",
        "QUEUED",
        "FAILED",
        "COMPLETED_WITH_ERRORS",
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
    @staticmethod
    def process(payroll_run, progress_callback=None):
        payroll_run.refresh_from_db()

        if payroll_run.status not in (
            PayrollProcessor.ALLOWED_STATUSES
            | {"PROCESSING"}
        ):
            raise ValueError(
                f"Payroll cannot be processed while its status is "
                f"{payroll_run.status}."
            )

        employees = (
            Employee.objects
            .filter(
                employment_status__in=[
                    "ACTIVE",
                    "PROBATION",
                    "ONBOARDING",
                ]
            )
            .order_by("id")
        )

        total = employees.count()
        processed = 0
        failed = 0
        failures = []

        payroll_run.total_employees = total
        payroll_run.processed_employees = 0
        payroll_run.failed_employees = 0
        payroll_run.progress_percentage = Decimal("0.00")
        payroll_run.failure_details = []

        payroll_run.save(
            update_fields=[
                "total_employees",
                "processed_employees",
                "failed_employees",
                "progress_percentage",
                "failure_details",
            ]
        )

        for employee in employees.iterator(chunk_size=100):
            try:
                with transaction.atomic():
                    generate_payslip(
                        payroll_run,
                        employee,
                    )

            except Exception as exc:
                failed += 1

                failure = {
                    "employee_id": employee.id,
                    "employee_name": employee.full_name,
                    "error": str(exc),
                }

                failures.append(failure)

                logger.exception(
                    "Payroll failed for employee %s in payroll run %s.",
                    employee.id,
                    payroll_run.id,
                )

            finally:
                processed += 1

                percentage = (
                    Decimal(processed)
                    / Decimal(total)
                    * Decimal("100.00")
                    if total
                    else Decimal("100.00")
                ).quantize(Decimal("0.01"))

                PayrollRun.objects.filter(
                    pk=payroll_run.pk
                ).update(
                    processed_employees=processed,
                    failed_employees=failed,
                    progress_percentage=percentage,
                    failure_details=failures,
                )

                if progress_callback:
                    progress_callback(
                        processed=processed,
                        total=total,
                        failed=failed,
                        percentage=percentage,
                    )

        payroll_run.refresh_from_db()
        payroll_run.processed_at = timezone.now()
        payroll_run.save(
            update_fields=[
                "processed_at",
            ]
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
        return {
            "payroll_run_id": payroll_run.id,
            "total": total,
            "processed": processed,
            "successful": processed - failed,
            "failed": failed,
            "failure_details": failures,
        }


@transaction.atomic
def submit_payroll_for_approval(
    payroll_run,
    submitted_by,
    comment="",
    request=None,
):
    if payroll_run.status != "COMPLETED":
        raise ValueError(
            "Only successfully completed payroll can be submitted "
            "for approval."
        )

    if payroll_run.failed_employees > 0:
        raise ValueError(
            "Payroll cannot be submitted because some employee "
            "records failed processing."
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

    if payroll_run.failed_employees > 0:
        raise ValueError(
            "Payroll cannot be finalized because it contains "
            "failed employee records."
        )

    if not payroll_run.payslips.exists():
        raise ValueError(
            "Payroll cannot be finalized because no payslips exist."
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
        Q(account_number="")
        | Q(account_number__isnull=True)
        | Q(bank_name="")
        | Q(account_name="")
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
