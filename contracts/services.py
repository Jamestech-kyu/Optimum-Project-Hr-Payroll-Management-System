from django.db import transaction
from django.utils import timezone

from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    ContractRenewal,
    ContractTermination,
)


@transaction.atomic
def renew_contract(
    contract,
    renewed_by,
    new_start_date,
    new_end_date,
    new_salary,
    reason="",
    request=None,
):
    if contract.status not in [
        "ACTIVE",
        "EXPIRED",
    ]:
        raise ValueError(
            "Only active or expired contracts can be renewed."
        )

    previous_end_date = contract.end_date
    previous_salary = contract.basic_salary

    renewal = ContractRenewal.objects.create(
        contract=contract,
        previous_end_date=previous_end_date,
        new_start_date=new_start_date,
        new_end_date=new_end_date,
        previous_salary=previous_salary,
        new_salary=new_salary,
        reason=reason,
        renewed_by=renewed_by,
    )

    contract.start_date = new_start_date
    contract.end_date = new_end_date
    contract.basic_salary = new_salary
    contract.status = "ACTIVE"

    contract.save(
        update_fields=[
            "start_date",
            "end_date",
            "basic_salary",
            "status",
            "updated_at",
        ]
    )

    employee = contract.employee

    employee.basic_salary = new_salary
    employee.employment_status = "ACTIVE"

    employee.save(
        update_fields=[
            "basic_salary",
            "employment_status",
            "updated_at",
        ]
    )

    log_activity(
        user=renewed_by,
        action="UPDATE",
        module="Contracts",
        description=(
            f"Renewed contract {contract.contract_number} "
            f"for employee {employee.employee_number}."
        ),
        object_id=contract.id,
        ip_address=(
            get_client_ip(request)
            if request
            else None
        ),
    )

    return renewal


@transaction.atomic
def terminate_contract(
    contract,
    terminated_by,
    termination_type,
    termination_date,
    reason,
    notice_period_days=0,
    final_settlement_required=True,
    request=None,
):
    if contract.status in [
        "TERMINATED",
        "CANCELLED",
    ]:
        raise ValueError(
            "This contract cannot be terminated again."
        )

    if termination_date < contract.start_date:
        raise ValueError(
            "Termination date cannot be before contract start date."
        )

    termination, _ = ContractTermination.objects.update_or_create(
        contract=contract,
        defaults={
            "termination_type": termination_type,
            "termination_date": termination_date,
            "reason": reason,
            "notice_period_days": notice_period_days,
            "final_settlement_required": (
                final_settlement_required
            ),
            "terminated_by": terminated_by,
        },
    )

    contract.status = "TERMINATED"
    contract.end_date = termination_date

    contract.save(
        update_fields=[
            "status",
            "end_date",
            "updated_at",
        ]
    )

    employee = contract.employee
    employee.employment_status = "TERMINATED"
    employee.termination_date = termination_date
    employee.termination_reason = reason

    employee.save(
        update_fields=[
            "employment_status",
            "termination_date",
            "termination_reason",
            "updated_at",
        ]
    )

    log_activity(
        user=terminated_by,
        action="UPDATE",
        module="Contracts",
        description=(
            f"Terminated contract {contract.contract_number} "
            f"for employee {employee.employee_number}. "
            f"Reason: {reason}"
        ),
        object_id=contract.id,
        ip_address=(
            get_client_ip(request)
            if request
            else None
        ),
    )

    return termination