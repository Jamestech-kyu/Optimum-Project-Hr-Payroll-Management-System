from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta

from employees.models import Employee
from attendance.models import AttendanceRecord
from leave_management.models import LeaveRequest
from payroll.models import Payslip
from performance.models import PerformanceReview
from training.models import (
    TrainingEnrollment,
    TrainingCertificate,
)
from contracts.models import EmploymentContract


def dashboard_overview():
    today = timezone.now().date()

    active_employees = Employee.objects.filter(
        employment_status="ACTIVE"
    ).count()

    total_employees = Employee.objects.count()

    return {
        "total_employees": total_employees,

        "active_employees": active_employees,

        "inactive_employees": total_employees - active_employees,

        "today_attendance": AttendanceRecord.objects.filter(
            date=today
        ).count(),

        "pending_leave_requests": LeaveRequest.objects.filter(
            status="PENDING"
        ).count(),

        "payroll_records": Payslip.objects.count(),

        "training_enrollments": TrainingEnrollment.objects.count(),

        "certificates_issued": TrainingCertificate.objects.count(),

        "contracts_expiring_30_days":
            EmploymentContract.objects.filter(
                end_date__gte=today,
                end_date__lte=today + timedelta(days=30),
            ).count(),
    }


def employee_statistics():
    return {
        "by_department": list(
            Employee.objects.values(
                "department__name"
            ).annotate(
                total=Count("id")
            )
        ),

        "by_branch": list(
            Employee.objects.values(
                "branch__name"
            ).annotate(
                total=Count("id")
            )
        ),
    }


def attendance_statistics():
    return {
        "status_distribution": list(
            AttendanceRecord.objects.values(
                "status"
            ).annotate(
                total=Count("id")
            )
        )
    }


def leave_statistics():
    return {
        "status_distribution": list(
            LeaveRequest.objects.values(
                "status"
            ).annotate(
                total=Count("id")
            )
        )
    }


def payroll_statistics():
    totals = Payslip.objects.aggregate(
        gross=Sum("gross_pay"),
        deductions=Sum("total_deductions"),
        net=Sum("net_pay"),
    )

    return totals


def performance_statistics():
    return PerformanceReview.objects.aggregate(
        average_score=Avg("overall_score")
    )


def training_statistics():
    return {
        "courses_completed":
            TrainingCertificate.objects.count(),

        "enrollments":
            TrainingEnrollment.objects.count(),

        "status_distribution":
            list(
                TrainingEnrollment.objects.values(
                    "status"
                ).annotate(
                    total=Count("id")
                )
            )
    }
