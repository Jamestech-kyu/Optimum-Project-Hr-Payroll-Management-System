import logging
from decimal import Decimal

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

        payment.bank_name = employee.bank_name
        payment.account_number = employee.bank_account_number
        payment.account_name = employee.bank_account_name

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
