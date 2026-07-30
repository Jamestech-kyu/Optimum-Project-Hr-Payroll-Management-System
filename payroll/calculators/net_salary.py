import calendar
from datetime import date
from decimal import Decimal

from .allowances import calculate_employee_allowances
from .basic_salary import calculate_employee_basic_salary
from .deductions import (
    calculate_employee_extra_components,
    calculate_statutory_deductions,
)
from .tax import calculate_paye


def get_payroll_period_end(payroll_run):
    last_day = calendar.monthrange(
        payroll_run.year,
        payroll_run.month,
    )[1]

    return date(
        payroll_run.year,
        payroll_run.month,
        last_day,
    )


def calculate_gross_pay(employee):
    basic_salary = calculate_employee_basic_salary(employee)
    total_allowances, allowances = calculate_employee_allowances(employee)
    extra_earnings, extra_deductions = calculate_employee_extra_components(
        employee,
        basic_salary,
    )

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


def calculate_employee_payroll(employee, payroll_run=None):
    gross_data = calculate_gross_pay(employee)

    gross_pay = gross_data["gross_pay"]
    taxable_income = gross_pay

    effective_date = (
        get_payroll_period_end(payroll_run)
        if payroll_run
        else None
    )

    paye = calculate_paye(
        taxable_income,
        effective_date=effective_date,
    )

    statutory_deductions = calculate_statutory_deductions(
        gross_pay,
        effective_date=effective_date,
    )
    extra_deductions = gross_data["extra_deductions"]

    total_deductions = (
        paye
        + sum(statutory_deductions.values(), Decimal("0.00"))
        + sum(extra_deductions.values(), Decimal("0.00"))
    )

    net_pay = gross_pay - total_deductions

    return {
        "basic_salary": gross_data["basic_salary"],
        "allowances": gross_data["allowances"],
        "extra_earnings": gross_data["extra_earnings"],
        "gross_pay": gross_pay.quantize(Decimal("0.01")),
        "paye": paye,
        "statutory_deductions": statutory_deductions,
        "extra_deductions": extra_deductions,
        "total_deductions": total_deductions.quantize(Decimal("0.01")),
        "net_pay": net_pay.quantize(Decimal("0.01")),
    }
