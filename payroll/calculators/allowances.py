from decimal import Decimal


def calculate_employee_allowances(employee):
    allowances = {
        "House Allowance": employee.house_allowance or Decimal("0.00"),
        "Transport Allowance": employee.transport_allowance or Decimal("0.00"),
        "Medical Allowance": employee.medical_allowance or Decimal("0.00"),
        "Other Allowance": employee.other_allowance or Decimal("0.00"),
    }

    total = sum(allowances.values(), Decimal("0.00"))

    return total, allowances
