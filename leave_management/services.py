from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from attendance.models import AttendanceRecord
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    LeaveBalance,
    LeaveRequest,
    LeaveApproval,
    PublicHoliday,
)


def calculate_working_days(start_date, end_date):
    """
    Count leave days excluding weekends and public holidays.
    """

    if end_date < start_date:
        raise ValueError("End date cannot be before start date.")

    total_days = Decimal("0.00")
    current_date = start_date

    holidays = set(
        PublicHoliday.objects.filter(
            date__range=[start_date, end_date]
        ).values_list("date", flat=True)
    )

    while current_date <= end_date:
        is_weekend = current_date.weekday() in [5, 6]

        if not is_weekend and current_date not in holidays:
            total_days += Decimal("1.00")

        current_date += timedelta(days=1)

    return total_days


def has_overlapping_leave(employee, start_date, end_date):
    """
    Check if employee already has pending or approved leave in same date range.
    """

    return LeaveRequest.objects.filter(
        employee=employee,
        start_date__lte=end_date,
        end_date__gte=start_date,
        status__in=[
            "PENDING_MANAGER",
            "PENDING_HR",
            "APPROVED",
        ],
    ).exists()


def get_leave_balance(employee, leave_type, year):
    """
    Get employee leave balance for a year.
    """

    try:
        return LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave_type,
            year=year,
        )
    except LeaveBalance.DoesNotExist:
        return None


def validate_leave_request(employee, leave_type, start_date, end_date):
    """
    Validate leave request before creation.
    """

    total_days = calculate_working_days(start_date, end_date)

    if total_days <= 0:
        raise ValueError("Leave request must include at least one working day.")

    if has_overlapping_leave(employee, start_date, end_date):
        raise ValueError("Employee already has an overlapping leave request.")

    balance = get_leave_balance(employee, leave_type, start_date.year)

    if not balance:
        raise ValueError("Leave balance not found for this employee and leave type.")

    if balance.remaining_days < total_days:
        raise ValueError("Insufficient leave balance.")

    return total_days


def create_leave_request(
    employee,
    leave_type,
    start_date,
    end_date,
    reason,
    requested_by,
    request=None,
):
    """
    Create a leave request after validation.
    """

    total_days = validate_leave_request(
        employee,
        leave_type,
        start_date,
        end_date,
    )

    leave_request = LeaveRequest.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        reason=reason,
        requested_by=requested_by,
        status="PENDING_MANAGER",
    )

    log_activity(
        user=requested_by,
        action="CREATE",
        module="Leave",
        description=f"Leave request created for {employee.full_name}.",
        object_id=leave_request.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return leave_request


def manager_approve_leave(leave_request, approver, comment="", request=None):
    """
    Manager approval moves request to HR approval stage.
    """

    if leave_request.status != "PENDING_MANAGER":
        raise ValueError("Leave request is not pending manager approval.")

    leave_request.status = "PENDING_HR"
    leave_request.manager_approved_by = approver
    leave_request.manager_approved_at = timezone.now()
    leave_request.save()

    LeaveApproval.objects.create(
        leave_request=leave_request,
        approver=approver,
        approval_level="MANAGER",
        action="APPROVED",
        comment=comment,
    )

    log_activity(
        user=approver,
        action="APPROVE",
        module="Leave",
        description=f"Manager approved leave request {leave_request.id}.",
        object_id=leave_request.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return leave_request


def hr_approve_leave(leave_request, approver, comment="", request=None):
    """
    HR final approval deducts balance and updates attendance.
    """

    if leave_request.status != "PENDING_HR":
        raise ValueError("Leave request is not pending HR approval.")

    balance = get_leave_balance(
        leave_request.employee,
        leave_request.leave_type,
        leave_request.start_date.year,
    )

    if not balance:
        raise ValueError("Leave balance not found.")

    if balance.remaining_days < leave_request.total_days:
        raise ValueError("Insufficient leave balance.")

    balance.used_days += leave_request.total_days
    balance.remaining_days = balance.allocated_days - balance.used_days
    balance.save()

    leave_request.status = "APPROVED"
    leave_request.hr_approved_by = approver
    leave_request.hr_approved_at = timezone.now()
    leave_request.save()

    LeaveApproval.objects.create(
        leave_request=leave_request,
        approver=approver,
        approval_level="HR",
        action="APPROVED",
        comment=comment,
    )

    current_date = leave_request.start_date

    while current_date <= leave_request.end_date:
        if current_date.weekday() not in [5, 6]:
            AttendanceRecord.objects.update_or_create(
                employee=leave_request.employee,
                date=current_date,
                defaults={
                    "status": "ON_LEAVE",
                    "remarks": f"Approved {leave_request.leave_type.name}",
                },
            )

        current_date += timedelta(days=1)

    log_activity(
        user=approver,
        action="APPROVE",
        module="Leave",
        description=f"HR approved leave request {leave_request.id}.",
        object_id=leave_request.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return leave_request


def reject_leave(leave_request, approver, reason, request=None):
    """
    Reject leave at any approval stage.
    """

    if leave_request.status not in ["PENDING_MANAGER", "PENDING_HR"]:
        raise ValueError("Only pending leave requests can be rejected.")

    approval_level = "MANAGER" if leave_request.status == "PENDING_MANAGER" else "HR"

    leave_request.status = "REJECTED"
    leave_request.rejection_reason = reason
    leave_request.save()

    LeaveApproval.objects.create(
        leave_request=leave_request,
        approver=approver,
        approval_level=approval_level,
        action="REJECTED",
        comment=reason,
    )

    log_activity(
        user=approver,
        action="REJECT",
        module="Leave",
        description=f"Rejected leave request {leave_request.id}. Reason: {reason}",
        object_id=leave_request.id,
        ip_address=get_client_ip(request) if request else None,
    )

    return leave_request