from decimal import Decimal

from .utils import calculate_distance
from datetime import datetime
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
    """
    Determine whether an employee is on time or late.
    """

    now = timezone.localtime()

    today = timezone.localdate()

    shift_start = datetime.combine(
        today,
        shift.start_time,
    )

    shift_start = timezone.make_aware(shift_start)

    grace_time = shift_start + timezone.timedelta(
        minutes=shift.grace_period_minutes
    )

    if now <= grace_time:
        return "PRESENT"

    return "LATE"
