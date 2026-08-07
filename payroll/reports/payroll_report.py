from django.db.models import Sum


def payroll_run_summary(payroll_run):
    totals = payroll_run.payslips.aggregate(
        gross_pay=Sum("gross_pay"),
        total_deductions=Sum("total_deductions"),
        net_pay=Sum("net_pay"),
    )

    return {
        "payroll_run_id": payroll_run.id,
        "month": payroll_run.month,
        "year": payroll_run.year,
        "status": payroll_run.status,
        "employee_count": payroll_run.payslips.count(),
        "gross_pay": totals["gross_pay"] or 0,
        "total_deductions": totals["total_deductions"] or 0,
        "net_pay": totals["net_pay"] or 0,
    }
