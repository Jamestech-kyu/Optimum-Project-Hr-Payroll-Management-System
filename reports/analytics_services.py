"""
Analytics payloads for the Reports & Analytics dashboard in the web client.

The functions here return the exact shapes the React components declare (see
src/features/reports/components/*.tsx), camelCase keys included, so the client
consumes them without a translation layer. The older ``dashboard_services``
module is left untouched; it still backs the overview, attendance, leave and
training endpoints.

Every figure is derived from stored records. Where the schema has no source for
a number the value is reported honestly rather than invented: lists come back
empty instead of padded, and see ``payroll_analytics`` (no budget model) and
``compliance_analytics`` (no statutory filing model) for the two places where
that shows through.
"""

from calendar import month_abbr, monthrange
from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, Q, Sum
from django.db.models.functions import Coalesce

from benefits.models import BenefitPlan, EmployeeBenefit
from employees.models import Employee
from payroll.models import PayrollRun, Payslip
from performance.models import PerformanceCycle, PerformanceReview


ZERO = Decimal("0")

# A payroll run counts as filed once it has cleared approval.
FILED_RUN_STATUSES = ("APPROVED", "FINALIZED")

# Statutory obligations the compliance card reports on.
STATUTORY_CATEGORIES = ("PAYE", "NSSF", "NHIF/SHIF", "Housing Levy")

# Enrollment states that do not represent live cover.
INACTIVE_BENEFIT_STATUSES = (
    "CANCELLED",
    "TERMINATED",
    "REJECTED",
    "EXPIRED",
    "DECLINED",
)

# Buckets are (label, inclusive lower bound, exclusive upper bound) on a 1-5 scale.
RATING_BUCKETS = (
    ("5 - Exceptional", Decimal("4.5"), None),
    ("4 - Exceeds", Decimal("3.5"), Decimal("4.5")),
    ("3 - Meets", Decimal("2.5"), Decimal("3.5")),
    ("2 - Needs Improvement", Decimal("1.5"), Decimal("2.5")),
    ("1 - Underperforming", None, Decimal("1.5")),
)

TENURE_BUCKETS = (
    ("< 1 year", 0, 1),
    ("1-3 years", 1, 3),
    ("3-5 years", 3, 5),
    ("5+ years", 5, None),
)

DEFAULT_MONTH_SPAN = 6
MAX_MONTH_SPAN = 24


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _money(field):
    return Coalesce(
        Sum(field),
        ZERO,
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )


def _percentage(part, whole, places=1):
    if not whole:
        return 0.0
    return round(float(part) / float(whole) * 100, places)


def _as_float(value, places=2):
    return round(float(value or 0), places)


def _as_int(value):
    return int(value or 0)


def employee_scope(branch=None, department=None):
    """Employees matching the dashboard's branch/department filter.

    The client's FilterBar sends display names (and "all" for no filter), but
    ids and codes are accepted too so the same endpoints serve other callers.
    """
    queryset = Employee.objects.all()

    if branch and branch != "all":
        criteria = Q(branch__name__iexact=branch) | Q(branch__code__iexact=branch)
        if str(branch).isdigit():
            criteria |= Q(branch_id=int(branch))
        queryset = queryset.filter(criteria)

    if department and department != "all":
        criteria = Q(department__name__iexact=department) | Q(
            department__code__iexact=department
        )
        if str(department).isdigit():
            criteria |= Q(department_id=int(department))
        queryset = queryset.filter(criteria)

    return queryset


def _month_start(value):
    return date(value.year, value.month, 1)


def _month_end(year, month):
    return date(year, month, monthrange(year, month)[1])


def _shift_months(value, months):
    total = (value.year * 12 + value.month - 1) + months
    return date(total // 12, total % 12 + 1, 1)


def month_series(start=None, end=None):
    """Ordered ``(year, month)`` pairs covering the requested window.

    Falls back to the last ``DEFAULT_MONTH_SPAN`` months when no range is given,
    and is capped at ``MAX_MONTH_SPAN`` so a wide filter cannot fan out into
    hundreds of per-month queries.
    """
    today = date.today()
    last = _month_start(end or today)
    first = _month_start(start) if start else _shift_months(last, -(DEFAULT_MONTH_SPAN - 1))

    if first > last:
        first, last = last, first

    span = (last.year - first.year) * 12 + (last.month - first.month) + 1
    if span > MAX_MONTH_SPAN:
        first = _shift_months(last, -(MAX_MONTH_SPAN - 1))
        span = MAX_MONTH_SPAN

    return [
        ((cursor := _shift_months(first, offset)).year, cursor.month)
        for offset in range(span)
    ]


def _month_labels(months):
    """Short labels for a month series, disambiguated by year when it spans one."""
    multi_year = len({year for year, _ in months}) > 1
    return {
        (year, month): (
            f"{month_abbr[month]} {year % 100:02d}" if multi_year else month_abbr[month]
        )
        for year, month in months
    }


def _runs_for_months(months):
    criteria = Q()
    for year, month in months:
        criteria |= Q(year=year, month=month)
    if not months:
        return PayrollRun.objects.none()
    return PayrollRun.objects.filter(criteria)


# ---------------------------------------------------------------------------
# Workforce
# ---------------------------------------------------------------------------


def workforce_analytics(branch=None, department=None, start=None, end=None):
    employees = employee_scope(branch, department)
    months = month_series(start, end)
    labels = _month_labels(months)
    today = date.today()

    headcount = []
    for year, month in months:
        period_start = date(year, month, 1)
        period_end = _month_end(year, month)

        total = (
            employees.filter(hire_date__lte=period_end)
            .filter(
                Q(termination_date__isnull=True)
                | Q(termination_date__gt=period_end)
            )
            .count()
        )

        headcount.append(
            {
                "month": labels[(year, month)],
                "total": total,
                "newHires": employees.filter(
                    hire_date__gte=period_start, hire_date__lte=period_end
                ).count(),
                "exits": employees.filter(
                    termination_date__gte=period_start,
                    termination_date__lte=period_end,
                ).count(),
            }
        )

    exits_total = sum(item["exits"] for item in headcount)
    totals = [item["total"] for item in headcount if item["total"]]
    average_headcount = sum(totals) / len(totals) if totals else 0

    midpoint = len(headcount) // 2
    earlier_exits = sum(item["exits"] for item in headcount[:midpoint])
    later_exits = sum(item["exits"] for item in headcount[midpoint:])
    if later_exits > earlier_exits:
        turnover_trend = "increasing"
    elif later_exits < earlier_exits:
        turnover_trend = "decreasing"
    else:
        turnover_trend = "stable"

    turnover_rate = _percentage(exits_total, average_headcount)

    active = employees.filter(employment_status="ACTIVE")
    tenures = [
        (today - hire_date).days / 365.25
        for hire_date in active.values_list("hire_date", flat=True)
        if hire_date
    ]
    tenure_distribution = [
        {
            "label": label,
            "value": sum(
                1
                for years in tenures
                if years >= lower and (upper is None or years < upper)
            ),
        }
        for label, lower, upper in TENURE_BUCKETS
    ]

    departments = []
    department_rows = (
        active.values("department__name")
        .order_by("department__name")
        .distinct()
    )
    for row in department_rows:
        name = row["department__name"] or "Unassigned"
        members = active.filter(department__name=row["department__name"])
        member_count = members.count()
        manager_count = (
            members.exclude(manager__isnull=True)
            .values("manager")
            .order_by()
            .distinct()
            .count()
        )
        departments.append(
            {
                "name": name,
                "headcount": member_count,
                "spanOfControl": (
                    round(member_count / manager_count, 1) if manager_count else 0
                ),
            }
        )

    active_total = active.count()
    diversity = []
    gender_rows = (
        active.values("gender").order_by("gender").distinct()
    )
    for row in gender_rows:
        count = active.filter(gender=row["gender"]).count()
        diversity.append(
            {
                "category": (row["gender"] or "Not specified").replace("_", " ").title(),
                "count": count,
                "percentage": _percentage(count, active_total),
            }
        )

    return {
        "headcount": headcount,
        "turnover": {"rate": turnover_rate, "trend": turnover_trend},
        "tenure": {
            "average": round(sum(tenures) / len(tenures), 1) if tenures else 0,
            "distribution": tenure_distribution,
        },
        "departments": departments,
        "diversity": diversity,
        "totalEmployees": employees.count(),
        "activeEmployees": active_total,
        "turnoverRate": turnover_rate,
        "newHires": sum(item["newHires"] for item in headcount),
        "exits": exits_total,
    }


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------


def payroll_analytics(branch=None, department=None, start=None, end=None):
    employees = employee_scope(branch, department)
    months = month_series(start, end)
    labels = _month_labels(months)

    payslips = Payslip.objects.filter(
        employee__in=employees,
        payroll_run__in=_runs_for_months(months),
    )

    monthly = []
    for year, month in months:
        aggregate = payslips.filter(
            payroll_run__year=year, payroll_run__month=month
        ).aggregate(gross=_money("gross_pay"))
        monthly.append(
            {
                "month": labels[(year, month)],
                "amount": _as_float(aggregate["gross"]),
            }
        )

    totals = payslips.aggregate(
        basic=_money("basic_salary"),
        allowances=_money("total_allowances"),
        gross=_money("gross_pay"),
        deductions=_money("total_deductions"),
        tax=_money("tax_amount"),
        net=_money("net_pay"),
    )

    other_deductions = (totals["deductions"] or ZERO) - (totals["tax"] or ZERO)
    components = (
        ("Basic Salary", totals["basic"]),
        ("Allowances", totals["allowances"]),
        ("Tax (PAYE)", totals["tax"]),
        ("Other Deductions", max(other_deductions, ZERO)),
    )
    component_total = sum((value or ZERO) for _, value in components)
    breakdown = [
        {
            "category": category,
            "amount": _as_float(value),
            "percentage": _percentage(value or ZERO, component_total),
        }
        for category, value in components
    ]

    branch_comparison = []
    branch_rows = (
        employees.values("branch__name").order_by("branch__name").distinct()
    )
    for row in branch_rows:
        branch_payslips = payslips.filter(employee__branch__name=row["branch__name"])
        branch_total = branch_payslips.aggregate(gross=_money("gross_pay"))["gross"]
        headcount = (
            branch_payslips.values("employee").order_by().distinct().count()
        )
        branch_comparison.append(
            {
                "branch": row["branch__name"] or "Unassigned",
                "totalPayroll": _as_float(branch_total),
                "avgPerEmployee": (
                    _as_float((branch_total or ZERO) / headcount) if headcount else 0
                ),
            }
        )

    gross = totals["gross"] or ZERO

    return {
        "total": monthly,
        "breakdown": breakdown,
        # No approved-budget model exists yet, so the budget is reported as the
        # actual spend with a zero variance rather than a made-up target.
        "budget": {
            "actual": _as_float(gross),
            "budget": _as_float(gross),
            "variance": 0.0,
        },
        "branchComparison": branch_comparison,
        "totalPayroll": f"KES {_as_int(gross):,}",
        "totalGross": _as_float(gross),
        "totalNet": _as_float(totals["net"]),
        "totalDeductions": _as_float(totals["deductions"]),
        "payslipCount": payslips.count(),
    }


# ---------------------------------------------------------------------------
# Statutory compliance
# ---------------------------------------------------------------------------


def compliance_analytics(branch=None, department=None, start=None, end=None):
    """Compliance standing inferred from payroll run approval state.

    There is no statutory filing model yet, so a run that has cleared approval
    is treated as filed and the four statutory categories share that basis.
    Once filings are modelled per obligation this should read from them
    directly, which is also what would make the per-category rows differ.
    """
    employees = employee_scope(branch, department)
    months = month_series(start, end)
    labels = _month_labels(months)
    today = date.today()

    runs = _runs_for_months(months)
    total_runs = runs.count()
    filed_runs = runs.filter(status__in=FILED_RUN_STATUSES).count()
    pending_runs = total_runs - filed_runs

    status_rows = [
        {
            "category": category,
            "filed": filed_runs,
            "pending": pending_runs,
            "total": total_runs,
        }
        for category in STATUTORY_CATEGORIES
    ]

    payslips = Payslip.objects.filter(employee__in=employees, payroll_run__in=runs)
    trend = []
    for year, month in months:
        aggregate = payslips.filter(
            payroll_run__year=year, payroll_run__month=month
        ).aggregate(statutory=_money("tax_amount"))
        trend.append(
            {
                "month": labels[(year, month)],
                "amount": _as_float(aggregate["statutory"]),
            }
        )

    flags = []
    outstanding = runs.exclude(status__in=FILED_RUN_STATUSES).exclude(
        status="CANCELLED"
    )
    for run in outstanding.order_by("year", "month"):
        run_branches = (
            employees.filter(payslips__payroll_run=run)
            .values_list("branch__name", flat=True)
            .order_by()
            .distinct()
        )
        period = f"{month_abbr[run.month]} {run.year}"
        is_overdue = (run.year, run.month) < (today.year, today.month)
        for branch_name in run_branches:
            flags.append(
                {
                    "branch": branch_name or "Unassigned",
                    "issue": f"{period} payroll not approved",
                    "status": "overdue" if is_overdue else "pending",
                }
            )

    return {
        "status": status_rows,
        "trend": trend,
        "flags": flags,
        "overallScore": _percentage(filed_runs, total_runs),
        "filedRuns": filed_runs,
        "pendingRuns": pending_runs,
        "totalRuns": total_runs,
    }


# ---------------------------------------------------------------------------
# Benefits
# ---------------------------------------------------------------------------


def benefits_analytics(branch=None, department=None, start=None, end=None):
    employees = employee_scope(branch, department)
    active = employees.filter(employment_status="ACTIVE")
    eligible = active.count()

    enrollments = EmployeeBenefit.objects.filter(employee__in=employees).exclude(
        status__in=INACTIVE_BENEFIT_STATUSES
    )

    summary = []
    total_cost = ZERO
    for plan in BenefitPlan.objects.filter(is_active=True).order_by("name"):
        plan_enrollments = enrollments.filter(benefit_plan=plan)
        enrolled = (
            plan_enrollments.values("employee").order_by().distinct().count()
        )
        cost = plan_enrollments.aggregate(
            employee_share=_money("employee_amount"),
            employer_share=_money("employer_amount"),
        )
        plan_cost = (cost["employee_share"] or ZERO) + (cost["employer_share"] or ZERO)
        total_cost += plan_cost

        summary.append(
            {
                "category": plan.name,
                "utilization": _percentage(enrolled, eligible, places=0),
                "cost": _as_float(plan_cost),
                "eligible": eligible,
                "enrolled": enrolled,
            }
        )

    enrolled_total = (
        enrollments.values("employee").order_by().distinct().count()
    )

    return {
        "summary": summary,
        "totalCost": _as_float(total_cost),
        "avgUtilization": _percentage(enrolled_total, eligible, places=0),
        "totalEligible": eligible,
        "totalEnrolled": enrolled_total,
    }


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def performance_analytics(branch=None, department=None, start=None, end=None):
    employees = employee_scope(branch, department)
    reviews = PerformanceReview.objects.filter(employee__in=employees)

    if start:
        reviews = reviews.filter(review_date__gte=start)
    if end:
        reviews = reviews.filter(review_date__lte=end)

    total_reviews = reviews.count()

    distribution = []
    for label, lower, upper in RATING_BUCKETS:
        bucket = reviews
        if lower is not None:
            bucket = bucket.filter(overall_score__gte=lower)
        if upper is not None:
            bucket = bucket.filter(overall_score__lt=upper)
        count = bucket.count()
        distribution.append(
            {
                "rating": label,
                "count": count,
                "percentage": _percentage(count, total_reviews),
            }
        )

    department_comparison = []
    department_rows = (
        reviews.values("employee__department__name")
        .order_by("employee__department__name")
        .distinct()
    )
    for row in department_rows:
        name = row["employee__department__name"]
        scores = reviews.filter(employee__department__name=name).values_list(
            "overall_score", flat=True
        )
        scores = [score for score in scores if score is not None]
        department_comparison.append(
            {
                "department": name or "Unassigned",
                "avgScore": (
                    round(float(sum(scores)) / len(scores), 2) if scores else 0
                ),
            }
        )

    trend = []
    cycle_ids = reviews.values_list("cycle_id", flat=True).order_by().distinct()
    for cycle in PerformanceCycle.objects.filter(id__in=cycle_ids).order_by(
        "start_date"
    ):
        scores = reviews.filter(cycle=cycle).values_list("overall_score", flat=True)
        scores = [score for score in scores if score is not None]
        trend.append(
            {
                "cycle": cycle.title,
                "avgScore": round(float(sum(scores)) / len(scores), 2) if scores else 0,
            }
        )

    all_scores = [
        score
        for score in reviews.values_list("overall_score", flat=True)
        if score is not None
    ]

    return {
        "distribution": distribution,
        "departmentComparison": department_comparison,
        "trend": trend,
        "overallAvg": (
            round(float(sum(all_scores)) / len(all_scores), 2) if all_scores else 0
        ),
        "reviewCount": total_reviews,
    }
