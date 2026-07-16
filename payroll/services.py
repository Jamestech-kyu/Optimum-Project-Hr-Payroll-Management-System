from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from .models import (
    DeductionType,
    Payroll,
    PayrollDeduction,
    PayrollRun,
    SalaryStructure,
    TaxSlab,
)


def run_payroll_for_run(payroll_run: PayrollRun):
    # only active employees
    from employees.models import Employee

    active_employees = Employee.objects.filter(employment_status='ACTIVE')

    for employee in active_employees:
        run_payroll_for_employee(payroll_run, employee)


def run_payroll_for_employee(payroll_run: PayrollRun, employee):
    # get latest active salary structure
    from datetime import date

    today = date.today()

    latest_structure = (
        SalaryStructure.objects.filter(employee=employee)
        .filter(effective_from__lte=today)
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
        .order_by('-effective_from')
        .first()
    )

    if latest_structure is None:
        return

    # compute gross pay
    gross_pay = (
        latest_structure.basic_salary
        + latest_structure.housing_allowance
        + latest_structure.transport_allowance
        + latest_structure.other_allowances
    )

    # compute PAYE/progressive tax
    tax_slabs = TaxSlab.objects.filter(is_active=True).order_by('order_index')
    taxable = Decimal(gross_pay)
    total_tax = Decimal('0')

    for slab in tax_slabs:
        lower = Decimal(slab.lower_bound)
        upper = Decimal(slab.upper_bound) if slab.upper_bound is not None else None
        if taxable <= lower:
            continue

        slab_taxable = taxable - lower
        if upper is not None:
            cap = upper - lower
            slab_taxable = min(slab_taxable, cap)

        slab_tax = (slab_taxable * Decimal(slab.rate_percent)) / Decimal('100')
        total_tax += slab_tax

        if upper is not None and taxable <= upper:
            break

    # total deductions (tax + other active deductions)
    deduction_rows = []

    # include PAYE as statutory deduction? Not modeled explicitly; treat as PayrollDeduction with a synthetic type.
    # If you later add a dedicated DeductionType for PAYE, this can be adjusted.
    deduction_rows.append(("PAYE", total_tax, f"Progressive slabs from gross={gross_pay}"))

    for dt in DeductionType.objects.filter(is_active=True):
        if dt.calculation_type == dt.CALC_PERCENT:
            amount = (Decimal(dt.rate_or_amount) * Decimal(gross_pay)) / Decimal('100')
            basis = f"{dt.name}: {dt.rate_or_amount}% of gross {gross_pay}"
        else:
            amount = Decimal(dt.rate_or_amount)
            basis = f"{dt.name}: fixed {dt.rate_or_amount}"

        deduction_rows.append((dt.name, amount, basis))

    total_deductions = sum(amount for _, amount, _ in deduction_rows)
    net_pay = Decimal(gross_pay) - Decimal(total_deductions)

    with transaction.atomic():
        # idempotency
        payroll = Payroll.objects.filter(payroll_run=payroll_run, employee=employee).first()
        if payroll is None:
            payroll = Payroll.objects.create(
                payroll_run=payroll_run,
                employee=employee,
                salary_structure=latest_structure,
                gross_pay=gross_pay,
                total_deductions=total_deductions,
                net_pay=net_pay,
            )
        else:
            payroll.salary_structure = latest_structure
            payroll.gross_pay = gross_pay
            payroll.total_deductions = total_deductions
            payroll.net_pay = net_pay
            payroll.save()

        PayrollDeduction.objects.filter(payroll=payroll).delete()

        # write deductions
        for name, amount, basis in deduction_rows:
            # map to DeductionType if exists; otherwise skip FK requirements by creating placeholder None
            dt = DeductionType.objects.filter(name=name).first()
            if dt is None:
                continue

            PayrollDeduction.objects.create(
                payroll=payroll,
                deduction_type=dt,
                amount=amount,
                calculation_basis=basis,
            )



