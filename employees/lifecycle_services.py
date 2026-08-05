"""
Employee lifecycle payload for the web client's Employee Lifecycle page.

Returns ``{"employees": [...], "analytics": {...}}`` in the exact shape the page
declares (see src/features/employees/lifecycle/pages/EmployeeLifecyclePage.tsx),
camelCase keys included.

Milestones are assembled from stored records only. Each contributing table is
read once and grouped in memory rather than queried per employee, so the whole
payload costs a fixed handful of queries regardless of headcount.
"""

from collections import defaultdict
from datetime import date

from django.db.models import Q

from benefits.models import EmployeeBenefit
from hr_operations.models import OffboardingCase
from payroll.models import Payslip
from performance.models import PerformanceReview

from .models import Employee, SalaryHistory


# Lifecycle stages the client renders, keyed off employment_status. Employees
# with an open offboarding case are promoted to "notice_period" below.
STAGE_BY_STATUS = {
    "ONBOARDING": "onboarding",
    "PROBATION": "active",
    "ACTIVE": "active",
    "SUSPENDED": "active",
    "TERMINATED": "offboarded",
    "OFFBOARDED": "offboarded",
}

STAGE_LABELS = {
    "onboarding": "Onboarding",
    "active": "Active",
    "notice_period": "Notice Period",
    "offboarded": "Offboarding Complete",
}

CLOSED_OFFBOARDING_STATUSES = ("COMPLETED", "CANCELLED")

DAYS_PER_YEAR = 365.25


def _full_name(employee):
    parts = [employee.first_name, employee.middle_name, employee.last_name]
    return " ".join(part for part in parts if part) or employee.employee_number


def _duration_label(days):
    """Human duration used by the analytics tiles."""
    if not days:
        return "Not recorded"
    if days < 60:
        return f"{int(round(days))} days"
    if days < DAYS_PER_YEAR:
        return f"{int(round(days / 30))} months"
    return f"{days / DAYS_PER_YEAR:.1f} years"


def _percentage(part, whole):
    if not whole:
        return 0.0
    return round(float(part) / float(whole) * 100, 1)


def _filtered_employees(
    search=None,
    department=None,
    branch=None,
    employment_type=None,
    visible_employee_ids=None,
):
    queryset = Employee.objects.select_related(
        "branch",
        "department",
        "designation",
    ).order_by("employee_number")

    if visible_employee_ids is not None:
        queryset = queryset.filter(id__in=visible_employee_ids)

    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search)
            | Q(middle_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(employee_number__icontains=search)
            | Q(work_email__icontains=search)
            | Q(personal_email__icontains=search)
        )

    if department and department != "all":
        criteria = Q(department__name__iexact=department) | Q(
            department__code__iexact=department
        )
        if str(department).isdigit():
            criteria |= Q(department_id=int(department))
        queryset = queryset.filter(criteria)

    if branch and branch != "all":
        criteria = Q(branch__name__iexact=branch) | Q(branch__code__iexact=branch)
        if str(branch).isdigit():
            criteria |= Q(branch_id=int(branch))
        queryset = queryset.filter(criteria)

    if employment_type and employment_type != "all":
        queryset = queryset.filter(employment_type__iexact=employment_type)

    return queryset


def _group_milestones(employee_ids):
    """Milestones for the given employees, grouped by employee id."""
    grouped = defaultdict(list)

    salary_changes = SalaryHistory.objects.filter(
        employee_id__in=employee_ids
    ).select_related("employee")
    for change in salary_changes:
        is_promotion = change.adjustment_type == "PROMOTION"
        grouped[change.employee_id].append(
            {
                "id": f"salary-{change.id}",
                "type": "promotion" if is_promotion else "salary",
                "date": change.effective_date.isoformat(),
                "title": change.get_adjustment_type_display(),
                "description": (
                    change.reason
                    or f"Salary changed to {change.new_salary}."
                ),
                "moduleLink": "/employee-finance",
                "details": {
                    "previousSalary": float(change.previous_salary or 0),
                    "newSalary": float(change.new_salary or 0),
                },
            }
        )

    reviews = PerformanceReview.objects.filter(
        employee_id__in=employee_ids
    ).select_related("cycle")
    for review in reviews:
        grouped[review.employee_id].append(
            {
                "id": f"review-{review.id}",
                "type": "performance",
                "date": review.review_date.isoformat(),
                "title": (
                    f"{review.cycle.title} review"
                    if review.cycle_id
                    else "Performance review"
                ),
                "description": (
                    review.overall_rating
                    or f"Overall score {review.overall_score}."
                ),
                "moduleLink": "/performance-oversight",
                "details": {
                    "overallScore": float(review.overall_score or 0),
                    "status": review.status,
                },
            }
        )

    enrollments = EmployeeBenefit.objects.filter(
        employee_id__in=employee_ids
    ).select_related("benefit_plan")
    for enrollment in enrollments:
        grouped[enrollment.employee_id].append(
            {
                "id": f"benefit-{enrollment.id}",
                "type": "benefits",
                "date": enrollment.enrollment_date.isoformat(),
                "title": f"Enrolled in {enrollment.benefit_plan.name}",
                "description": enrollment.remarks or "Benefit enrollment recorded.",
                "moduleLink": "/benefits-management",
                "details": {"status": enrollment.status},
            }
        )

    # Only the most recent payslip per employee: the full history would swamp
    # the timeline without telling the reader anything new.
    latest_payslips = {}
    payslips = Payslip.objects.filter(
        employee_id__in=employee_ids
    ).select_related("payroll_run")
    for payslip in payslips:
        run = payslip.payroll_run
        key = (run.year, run.month)
        current = latest_payslips.get(payslip.employee_id)
        if current is None or key > current[0]:
            latest_payslips[payslip.employee_id] = (key, payslip)

    for employee_id, ((year, month), payslip) in latest_payslips.items():
        grouped[employee_id].append(
            {
                "id": f"payslip-{payslip.id}",
                "type": "payroll",
                "date": date(year, month, 1).isoformat(),
                "title": "Latest payslip issued",
                "description": f"Net pay {payslip.net_pay} for {month}/{year}.",
                "moduleLink": "/payroll-history",
                "details": {
                    "grossPay": float(payslip.gross_pay or 0),
                    "netPay": float(payslip.net_pay or 0),
                },
            }
        )

    cases = OffboardingCase.objects.filter(employee_id__in=employee_ids)
    for case in cases:
        grouped[case.employee_id].append(
            {
                "id": f"offboarding-{case.id}",
                "type": "offboarding",
                "date": case.last_working_day.isoformat(),
                "title": f"Offboarding - {case.get_exit_type_display()}",
                "description": case.reason or "Offboarding case opened.",
                "moduleLink": "/employee-offboarding",
                "details": {"status": case.status},
            }
        )

    return grouped


def _open_offboarding_employee_ids(employee_ids):
    return set(
        OffboardingCase.objects.filter(employee_id__in=employee_ids)
        .exclude(status__in=CLOSED_OFFBOARDING_STATUSES)
        .values_list("employee_id", flat=True)
        .order_by()
        .distinct()
    )


def employee_lifecycle(
    search=None,
    stage=None,
    department=None,
    branch=None,
    employment_type=None,
    visible_employee_ids=None,
):
    queryset = _filtered_employees(
        search,
        department,
        branch,
        employment_type,
        visible_employee_ids,
    )
    records = list(queryset)
    employee_ids = [employee.id for employee in records]
    today = date.today()

    milestones_by_employee = _group_milestones(employee_ids)
    serving_notice = _open_offboarding_employee_ids(employee_ids)

    employees = []
    for employee in records:
        resolved_stage = STAGE_BY_STATUS.get(employee.employment_status, "active")
        if employee.id in serving_notice and resolved_stage != "offboarded":
            resolved_stage = "notice_period"

        milestones = list(milestones_by_employee.get(employee.id, []))

        if employee.hire_date:
            milestones.append(
                {
                    "id": f"hire-{employee.id}",
                    "type": "hire",
                    "date": employee.hire_date.isoformat(),
                    "title": "Joined the company",
                    "description": (
                        f"{employee.designation.title if employee.designation else 'Employee'}"
                        f" in {employee.department.name if employee.department else 'Unassigned'}."
                    ),
                    "moduleLink": "/employee-management",
                    "details": {"employeeNumber": employee.employee_number},
                }
            )

        if employee.probation_end_date:
            milestones.append(
                {
                    "id": f"probation-{employee.id}",
                    "type": "probation",
                    "date": employee.probation_end_date.isoformat(),
                    "title": (
                        "Probation completed"
                        if employee.probation_end_date <= today
                        else "Probation ends"
                    ),
                    "description": (
                        f"Confirmed on {employee.confirmation_date.isoformat()}."
                        if employee.confirmation_date
                        else "Probation period milestone."
                    ),
                    "moduleLink": "/employee-management",
                    "details": {},
                }
            )

        if employee.termination_date:
            milestones.append(
                {
                    "id": f"exit-{employee.id}",
                    "type": "offboarding",
                    "date": employee.termination_date.isoformat(),
                    "title": "Left the company",
                    "description": "Termination recorded.",
                    "moduleLink": "/employee-offboarding",
                    "details": {},
                }
            )

        milestones.sort(key=lambda item: item["date"])
        today_iso = today.isoformat()

        upcoming = [
            {
                "id": item["id"],
                "type": item["type"],
                "date": item["date"],
                "title": item["title"],
            }
            for item in milestones
            if item["date"] > today_iso
        ]

        # The client falls back to a default icon when none is supplied.
        activity = [
            {"date": item["date"], "text": item["title"]}
            for item in reversed(milestones)
            if item["date"] <= today_iso
        ][:6]

        employees.append(
            {
                "id": str(employee.id),
                "name": _full_name(employee),
                "email": employee.work_email or employee.personal_email or "",
                "phone": employee.phone_number or "",
                "department": (
                    employee.department.name if employee.department else "Unassigned"
                ),
                "branch": employee.branch.name if employee.branch else "Unassigned",
                "role": employee.designation.title if employee.designation else "",
                "stage": resolved_stage,
                "startDate": (
                    employee.hire_date.isoformat() if employee.hire_date else ""
                ),
                "employmentType": employee.get_employment_type_display(),
                "employeeNumber": employee.employee_number,
                "milestones": milestones,
                "upcomingMilestones": upcoming,
                "activity": activity,
            }
        )

    if stage and stage != "all":
        employees = [item for item in employees if item["stage"] == stage]

    return {
        "employees": employees,
        "analytics": _analytics(records, employees, today),
    }


def _analytics(records, employees, today):
    stage_counts = defaultdict(int)
    for item in employees:
        stage_counts[item["stage"]] += 1

    stage_distribution = [
        {"stage": STAGE_LABELS[key], "count": stage_counts.get(key, 0)}
        for key in ("onboarding", "active", "notice_period", "offboarded")
    ]

    hire_dates = {
        employee.id: employee.hire_date for employee in records if employee.hire_date
    }

    # Time to promotion: gap between hire and the first recorded promotion.
    promotion_gaps = []
    promotions = (
        SalaryHistory.objects.filter(
            employee_id__in=hire_dates.keys(),
            adjustment_type="PROMOTION",
        )
        .values_list("employee_id", "effective_date")
        .order_by("employee_id", "effective_date")
    )
    first_promotion = {}
    for employee_id, effective_date in promotions:
        if employee_id not in first_promotion:
            first_promotion[employee_id] = effective_date
    for employee_id, effective_date in first_promotion.items():
        hire_date = hire_dates.get(employee_id)
        if hire_date and effective_date >= hire_date:
            promotion_gaps.append((effective_date - hire_date).days)

    active_records = [
        employee
        for employee in records
        if employee.employment_status in ("ACTIVE", "PROBATION", "SUSPENDED")
        and employee.hire_date
    ]
    tenure_days = [(today - employee.hire_date).days for employee in active_records]

    # Time to productivity: hire through to confirmation.
    confirmation_gaps = [
        (employee.confirmation_date - employee.hire_date).days
        for employee in records
        if employee.confirmation_date
        and employee.hire_date
        and employee.confirmation_date >= employee.hire_date
    ]

    # Onboarding completion measured over the last year of hires, so a long tail
    # of historic staff cannot mask a stalled current intake.
    recent_hires = [
        employee
        for employee in records
        if employee.hire_date
        and (today - employee.hire_date).days <= DAYS_PER_YEAR
    ]
    completed_onboarding = [
        employee
        for employee in recent_hires
        if employee.employment_status != "ONBOARDING"
    ]

    # Attrition is grouped by recorded exit reason; the schema stores exit type
    # rather than the stage an employee was in when they left.
    exit_rows = OffboardingCase.objects.filter(
        employee_id__in=[employee.id for employee in records]
    ).values_list("exit_type", flat=True)
    exit_counts = defaultdict(int)
    for exit_type in exit_rows:
        exit_counts[exit_type] += 1
    total_exits = sum(exit_counts.values())
    attrition_by_stage = [
        {
            "stage": exit_type.replace("_", " ").title(),
            "percentage": _percentage(count, total_exits),
        }
        for exit_type, count in sorted(
            exit_counts.items(), key=lambda pair: pair[1], reverse=True
        )
    ]

    return {
        "avgTimeToPromotion": _duration_label(
            sum(promotion_gaps) / len(promotion_gaps) if promotion_gaps else 0
        ),
        "avgTenure": _duration_label(
            sum(tenure_days) / len(tenure_days) if tenure_days else 0
        ),
        "attritionByStage": attrition_by_stage,
        "onboardingCompletionRate": _percentage(
            len(completed_onboarding), len(recent_hires)
        ),
        "timeToProductivity": _duration_label(
            sum(confirmation_gaps) / len(confirmation_gaps)
            if confirmation_gaps
            else 0
        ),
        "stageDistribution": stage_distribution,
        "totalEmployees": len(employees),
    }
