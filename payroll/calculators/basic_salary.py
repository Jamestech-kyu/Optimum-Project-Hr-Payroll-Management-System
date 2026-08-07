from decimal import Decimal


def calculate_employee_basic_salary(employee):
    return employee.basic_salary or Decimal("0.00")
