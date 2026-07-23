from django.db.models import Count, Sum
from django.utils import timezone

from employees.models import Employee
from attendance.models import AttendanceRecord
from leave_management.models import LeaveRequest
from payroll.models import Payslip
from training.models import TrainingEnrollment
from performance.models import PerformanceReview


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return "SUPER_ADMIN"

    role = getattr(user, "role", None)

    if role:
        return role.name

    return None


def super_admin_dashboard():
    today = timezone.now().date()

    return {
        "total_employees": Employee.objects.count(),
        "active_employees": Employee.objects.filter(
            employment_status="ACTIVE"
        ).count(),
        "today_attendance": AttendanceRecord.objects.filter(
            date=today
        ).count(),
        "pending_leave_requests": LeaveRequest.objects.filter(
            status="PENDING"
        ).count(),
        "total_payslips": Payslip.objects.count(),
        "training_enrollments": TrainingEnrollment.objects.count(),
        "performance_reviews": PerformanceReview.objects.count(),
    }


def hr_dashboard():
    return {
        "total_employees": Employee.objects.count(),
        "active_employees": Employee.objects.filter(
            employment_status="ACTIVE"
        ).count(),
        "onboarding_employees": Employee.objects.filter(
            employment_status="ONBOARDING"
        ).count(),
        "probation_employees": Employee.objects.filter(
            employment_status="PROBATION"
        ).count(),
        "pending_leave_requests": LeaveRequest.objects.filter(
            status="PENDING"
        ).count(),
        "training_enrollments": TrainingEnrollment.objects.count(),
        "performance_reviews": PerformanceReview.objects.count(),
    }


def payroll_dashboard():
    payroll_totals = Payslip.objects.aggregate(
        total_gross=Sum("gross_pay"),
        total_deductions=Sum("total_deductions"),
        total_net=Sum("net_pay"),
    )

    return {
        "total_payslips": Payslip.objects.count(),
        **payroll_totals,
    }


def manager_dashboard(user):
    employee = getattr(user, "employee_profile", None)

    if not employee:
        return {
            "team_members": 0,
            "pending_team_leave": 0,
            "team_attendance_today": 0,
        }

    team = Employee.objects.filter(manager=employee)
    today = timezone.now().date()

    return {
        "team_members": team.count(),

        "team_status_distribution": list(
            team.values("employment_status").annotate(
                total=Count("id")
            )
        ),

        "pending_team_leave": LeaveRequest.objects.filter(
            employee__in=team,
            status="PENDING",
        ).count(),

        "team_attendance_today": AttendanceRecord.objects.filter(
            employee__in=team,
            date=today,
        ).count(),
    }


def employee_dashboard(user):
    employee = getattr(user, "employee_profile", None)

    if not employee:
        return {
            "employee_profile_found": False,
        }

    return {
        "employee_profile_found": True,
        "employee_number": employee.employee_number,
        "employment_status": employee.employment_status,
        "leave_requests": LeaveRequest.objects.filter(
            employee=employee
        ).count(),
        "attendance_records": AttendanceRecord.objects.filter(
            employee=employee
        ).count(),
        "payslips": Payslip.objects.filter(
            employee=employee
        ).count(),
        "training_enrollments": TrainingEnrollment.objects.filter(
            employee=employee
        ).count(),
    }


def get_role_dashboard(user):
    role = get_user_role(user)

    if role in ["SUPER_ADMIN", "ADMIN"]:
        return {
            "role": role,
            "dashboard": super_admin_dashboard(),
        }

    if role == "HR":
        return {
            "role": role,
            "dashboard": hr_dashboard(),
        }

    if role == "PAYROLL_OFFICER":
        return {
            "role": role,
            "dashboard": payroll_dashboard(),
        }

    if role == "MANAGER":
        return {
            "role": role,
            "dashboard": manager_dashboard(user),
        }

    if role == "EMPLOYEE":
        return {
            "role": role,
            "dashboard": employee_dashboard(user),
        }

    return {
        "role": role,
        "dashboard": {},
        "message": "No dashboard configuration exists for this role.",
    }
