from django.db import transaction

from audit.services import log_activity
from audit.utils import get_client_ip
from contracts.models import EmploymentContract

from .models import SalaryHistory


@transaction.atomic
def adjust_employee_salary(
    employee,
    new_salary,
    adjustment_type,
    effective_date,
    reason,
    changed_by,
    update_active_contract=True,
    request=None,
):
    previous_salary = employee.basic_salary

    if new_salary == previous_salary:
        raise ValueError(
            "New salary must be different from the current salary."
        )

    history = SalaryHistory.objects.create(
        employee=employee,
        previous_salary=previous_salary,
        new_salary=new_salary,
        adjustment_type=adjustment_type,
        effective_date=effective_date,
        reason=reason,
        changed_by=changed_by,
    )

    employee.basic_salary = new_salary

    employee.save(
        update_fields=[
            "basic_salary",
            "updated_at",
        ]
    )

    if update_active_contract:
        active_contract = (
            EmploymentContract.objects.filter(
                employee=employee,
                status="ACTIVE",
            )
            .order_by("-start_date")
            .first()
        )

        if active_contract:
            active_contract.basic_salary = new_salary
            active_contract.save(
                update_fields=[
                    "basic_salary",
                    "updated_at",
                ]
            )

    log_activity(
        user=changed_by,
        action="UPDATE",
        module="Employees",
        description=(
            f"Adjusted salary for employee "
            f"{employee.employee_number} from "
            f"{previous_salary} to {new_salary}. "
            f"Reason: {reason}"
        ),
        object_id=employee.id,
        ip_address=(
            get_client_ip(request)
            if request
            else None
        ),
    )

    return history