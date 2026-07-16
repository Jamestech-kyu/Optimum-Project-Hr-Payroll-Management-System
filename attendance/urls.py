from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WorkLocationViewSet,
    ShiftViewSet,
    AttendanceRecordViewSet,
    AttendanceLocationLogViewSet,
    AttendanceCorrectionRequestViewSet,
    EmployeeAttendanceAssignmentViewSet,
    CheckInView,
    CheckOutView,
)

router = DefaultRouter()
router.register("work-locations", WorkLocationViewSet, basename="work-locations")
router.register("shifts", ShiftViewSet, basename="shifts")
router.register("records", AttendanceRecordViewSet, basename="attendance-records")
router.register("location-logs", AttendanceLocationLogViewSet, basename="attendance-location-logs")
router.register("correction-requests", AttendanceCorrectionRequestViewSet, basename="attendance-correction-requests")
router.register("assignments", EmployeeAttendanceAssignmentViewSet, basename="attendance-assignments")
router.register("employee-attendance-assignments", EmployeeAttendanceAssignmentViewSet, basename="employee-attendance")

urlpatterns = [
    path("", include(router.urls)),
    path("check-in/", CheckInView.as_view(), name="check-in"),
    path("check-out/", CheckOutView.as_view(), name="check-out"),
]
