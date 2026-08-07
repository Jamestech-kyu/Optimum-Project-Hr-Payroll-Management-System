from decimal import Decimal

from payroll.models import EmployeePayComponent


def calculate_employee_extra_earnings(employee):
    earnings = {}

    components = EmployeePayComponent.objects.filter(
        employee=employee,
        is_active=True,
        component__is_active=True,
        component__component_type="EARNING",
    )

    for item in components:
        component = item.component
        earnings[component.name] = (
            item.amount
            or component.default_amount
            or Decimal("0.00")
        )

    return earnings
