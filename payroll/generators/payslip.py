from decimal import Decimal

from payroll.calculators.net_salary import calculate_employee_payroll
from payroll.models import (
    BankPayment,
    PayrollAllowance,
    PayrollDeduction,
    Payslip,
)


def generate_payslip(payroll_run, employee):
    payroll_data = calculate_employee_payroll(
        employee,
        payroll_run=payroll_run,
    )

    payslip, created = Payslip.objects.update_or_create(
        payroll_run=payroll_run,
        employee=employee,
        defaults={
            "basic_salary": payroll_data["basic_salary"],
            "total_allowances": sum(
                payroll_data["allowances"].values(),
                Decimal("0.00"),
            )
            + sum(
                payroll_data["extra_earnings"].values(),
                Decimal("0.00"),
            ),
            "gross_pay": payroll_data["gross_pay"],
            "tax_amount": payroll_data["paye"],
            "total_deductions": payroll_data["total_deductions"],
            "net_pay": payroll_data["net_pay"],
        },
    )

    payslip.allowances.all().delete()
    payslip.deductions.all().delete()

    for name, amount in payroll_data["allowances"].items():
        PayrollAllowance.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    for name, amount in payroll_data["extra_earnings"].items():
        PayrollAllowance.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    PayrollDeduction.objects.create(
        payslip=payslip,
        name="PAYE",
        amount=payroll_data["paye"],
    )

    for name, amount in payroll_data["statutory_deductions"].items():
        PayrollDeduction.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    for name, amount in payroll_data["extra_deductions"].items():
        PayrollDeduction.objects.create(
            payslip=payslip,
            name=name,
            amount=amount,
        )

    bank_payment, payment_created = BankPayment.objects.get_or_create(
        payroll_run=payroll_run,
        employee=employee,
        defaults={
            "bank_name": employee.bank_name or "",
            "account_number": employee.bank_account_number or "",
            "account_name": employee.bank_account_name or "",
            "amount": payroll_data["net_pay"],
            "status": "PENDING",
        },
    )

    if not payment_created:
        if bank_payment.status == "PAID":
            raise ValueError(
                f"Cannot regenerate payroll for "
                f"{employee.full_name}; payment is already marked as paid."
            )

        bank_payment.bank_name = employee.bank_name or ""
        bank_payment.account_number = (
            employee.bank_account_number or ""
        )
        bank_payment.account_name = (
            employee.bank_account_name or ""
        )
        bank_payment.amount = payroll_data["net_pay"]
        bank_payment.status = "PENDING"

        bank_payment.save(
            update_fields=[
                "bank_name",
                "account_number",
                "account_name",
                "amount",
                "status",
            ]
        )

    return payslip
