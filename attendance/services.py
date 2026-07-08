from .utils import calculate_distance


def is_within_geofence(
    employee_lat,
    employee_lon,
    work_location,
):
    """
    Returns True if employee is inside the allowed geofence.
    """

    distance = calculate_distance(
        employee_lat,
        employee_lon,
        work_location.latitude,
        work_location.longitude,
    )

    return distance <= work_location.radius_meters