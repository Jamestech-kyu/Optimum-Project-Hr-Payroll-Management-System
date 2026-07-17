from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from employees.models import Employee

from .models import BenefitPlan, EmployeeBenefit


@transaction.atomic
def enroll_employee(
    *,
    employee_id,
    benefit_plan_id,
    enrollment_date,
    effective_date,
    end_date=None,
    employee_amount=0,
    employer_amount=0,
    remarks="",
    created_by=None,
    enrollment_window=None,
):
    employee = Employee.objects.get(id=employee_id)

    benefit_plan = BenefitPlan.objects.get(
        id=benefit_plan_id,
        is_active=True,
    )

    existing_enrollment = EmployeeBenefit.objects.filter(
        employee=employee,
        benefit_plan=benefit_plan,
        status__in=[
            "PENDING",
            "ACTIVE",
            "SUSPENDED",
        ],
    ).exists()

    if existing_enrollment:
        raise ValidationError(
            {
                "benefit_plan_id": (
                    "The employee already has an open enrollment "
                    "for this benefit plan."
                )
            }
        )

    if end_date and end_date < effective_date:
        raise ValidationError(
            {
                "end_date": (
                    "End date cannot be earlier than the effective date."
                )
            }
        )

    status_value = (
        "PENDING"
        if benefit_plan.requires_approval
        else "ACTIVE"
    )

    enrollment = EmployeeBenefit.objects.create(
        employee=employee,
        benefit_plan=benefit_plan,
        enrollment_window=enrollment_window,
        enrollment_date=enrollment_date,
        effective_date=effective_date,
        end_date=end_date,
        employee_amount=employee_amount,
        employer_amount=employer_amount,
        remarks=remarks,
        created_by=created_by,
        status=status_value,
    )

    return enrollment


@transaction.atomic
def approve_employee_benefit(
    *,
    enrollment,
    approved_by,
    remarks="",
):
    if enrollment.status != "PENDING":
        raise ValidationError(
            {
                "status": (
                    "Only pending benefit enrollments can be approved."
                )
            }
        )

    enrollment.status = "ACTIVE"
    enrollment.approved_by = approved_by
    enrollment.approved_at = timezone.now()

    if remarks:
        enrollment.remarks = remarks

    enrollment.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "remarks",
            "updated_at",
        ]
    )

    return enrollment


@transaction.atomic
def reject_employee_benefit(
    *,
    enrollment,
    approved_by,
    remarks="",
):
    if enrollment.status != "PENDING":
        raise ValidationError(
            {
                "status": (
                    "Only pending benefit enrollments can be rejected."
                )
            }
        )

    enrollment.status = "REJECTED"
    enrollment.approved_by = approved_by
    enrollment.approved_at = timezone.now()

    if remarks:
        enrollment.remarks = remarks

    enrollment.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "remarks",
            "updated_at",
        ]
    )

    return enrollment