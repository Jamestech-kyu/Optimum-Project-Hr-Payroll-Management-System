from decimal import Decimal

from payroll.models import EmployeePayComponent, StatutoryRate


def resolve_component_amount(item, base_amount):
    component = item.component

    if component.calculation_type == "PERCENTAGE":
        percentage = component.percentage_rate or Decimal("0.00")

        return (
            base_amount * percentage / Decimal("100.00")
        ).quantize(Decimal("0.01"))

    return (
        item.amount
        or component.default_amount
        or Decimal("0.00")
    ).quantize(Decimal("0.01"))


def calculate_employee_extra_components(employee, base_amount):
    earnings = {}
    deductions = {}

    components = EmployeePayComponent.objects.filter(
        employee=employee,
        is_active=True,
        component__is_active=True,
    ).select_related("component")

    for item in components:
        component = item.component
        amount = resolve_component_amount(item, base_amount)

        if component.component_type == "EARNING":
            earnings[component.name] = amount
        elif component.component_type in ["DEDUCTION", "TAX"]:
            deductions[component.name] = amount

    return earnings, deductions


def calculate_employee_extra_deductions(employee, base_amount=Decimal("0.00")):
    _, deductions = calculate_employee_extra_components(
        employee,
        base_amount,
    )

    return deductions


def calculate_statutory_deductions(
    gross_pay,
    effective_date=None,
):
    deductions = {}

    rates = StatutoryRate.objects.filter(is_active=True)

    if effective_date:
        rates = rates.filter(
            effective_from__lte=effective_date
        )

    latest_rates = {}

    for rate in rates.order_by(
        "code",
        "-effective_from",
    ):
        if rate.code not in latest_rates:
            latest_rates[rate.code] = rate

    for rate in latest_rates.values():
        if rate.is_percentage:
            amount = (
                gross_pay
                * rate.rate
                / Decimal("100.00")
            )
        else:
            amount = rate.rate

        deductions[rate.name] = amount.quantize(
            Decimal("0.01")
        )

    return deductions
