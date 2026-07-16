from decimal import Decimal

from .utils import calculate_distance
from datetime import datetime, timedelta
from django.utils import timezone


def get_geofence_result(
    employee_lat,
    employee_lon,
    work_location,
):
    """
    Calculate the employee's distance from the work location.

    Returns:
        {
            "distance_meters": Decimal,
            "within_geofence": bool,
        }
    """

    distance = calculate_distance(
        employee_lat,
        employee_lon,
        work_location.latitude,
        work_location.longitude,
    )

    distance_decimal = Decimal(str(round(distance, 2)))

    return {
        "distance_meters": distance_decimal,
        "within_geofence": distance <= work_location.radius_meters,
    }


def is_within_geofence(
    employee_lat,
    employee_lon,
    work_location,
):
    """
    Backward-compatible helper that returns only True or False.
    """

    result = get_geofence_result(
        employee_lat,
        employee_lon,
        work_location,
    )

    return result["within_geofence"]
def determine_attendance_status(shift):
    now = timezone.localtime()
    today = timezone.localdate()

    shift_start = datetime.combine(
        today,
        shift.start_time,
    )

    shift_start = timezone.make_aware(
        shift_start,
        timezone.get_current_timezone(),
    )

    grace_time = shift_start + timedelta(
        minutes=shift.grace_period_minutes
    )

    return "PRESENT" if now <= grace_time else "LATE"
def calculate_checkout_summary(attendance, checkout_time=None):
    """
    Calculate total worked hours, overtime hours, and final attendance status.
    Supports normal shifts and overnight shifts.
    """

    checkout_time = checkout_time or timezone.now()

    if not attendance.check_in_time:
        raise ValueError("Check-in time is missing.")

    total_seconds = (
        checkout_time - attendance.check_in_time
    ).total_seconds()

    total_hours = max(
        Decimal(str(total_seconds / 3600)),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))

    overtime_hours = Decimal("0.00")
    final_status = attendance.status

    if attendance.shift:
        local_checkout = timezone.localtime(checkout_time)
        attendance_date = attendance.date

        shift_start = datetime.combine(
            attendance_date,
            attendance.shift.start_time,
        )

        shift_end = datetime.combine(
            attendance_date,
            attendance.shift.end_time,
        )

        # Overnight shift, for example 18:00 to 06:00.
        if attendance.shift.end_time <= attendance.shift.start_time:
            shift_end += timedelta(days=1)

        current_timezone = timezone.get_current_timezone()

        shift_start = timezone.make_aware(
            shift_start,
            current_timezone,
        )

        shift_end = timezone.make_aware(
            shift_end,
            current_timezone,
        )

        if local_checkout < shift_end:
            final_status = "EARLY_LEAVE"

        elif local_checkout > shift_end:
            overtime_seconds = (
                local_checkout - shift_end
            ).total_seconds()

            overtime_hours = Decimal(
                str(overtime_seconds / 3600)
            ).quantize(Decimal("0.01"))

            # Preserve LATE if the employee arrived late.
            if attendance.status != "LATE":
                final_status = "OVERTIME"

    return {
        "checkout_time": checkout_time,
        "total_hours": total_hours,
        "overtime_hours": overtime_hours,
        "status": final_status,
    }
