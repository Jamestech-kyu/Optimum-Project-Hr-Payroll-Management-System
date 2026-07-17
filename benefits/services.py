from django.db import transaction

from employees.models import Employee

from .models import (
    BenefitPlan,
    EmployeeBenefit,
)


@transaction.atomic
def enroll_employee(
    *,
    employee_id,
    benefit_plan_id,
    enrollment_date,
    effective_date,
    end_date,
    employee_amount,
    employer_amount,
    remarks,
    created_by,
):
    employee = Employee.objects.get(
        id=employee_id,
    )

    benefit = BenefitPlan.objects.get(
        id=benefit_plan_id,
    )

    enrollment = EmployeeBenefit.objects.create(
        employee=employee,
        benefit_plan=benefit,
        enrollment_date=enrollment_date,
        effective_date=effective_date,
        end_date=end_date,
        employee_amount=employee_amount,
        employer_amount=employer_amount,
        remarks=remarks,
        created_by=created_by,
        status="ACTIVE",
    )

    return enrollment