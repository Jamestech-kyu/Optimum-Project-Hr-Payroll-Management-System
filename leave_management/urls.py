from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LeaveTypeViewSet,
    LeaveBalanceViewSet,
    LeaveRequestViewSet,
    LeaveApprovalViewSet,
    LeaveAttachmentViewSet,
    PublicHolidayViewSet,
    CreateLeaveRequestView,
    ManagerApproveLeaveView,
    HRApproveLeaveView,
    RejectLeaveView,
)

router = DefaultRouter()
router.register("types", LeaveTypeViewSet, basename="leave-types")
router.register("balances", LeaveBalanceViewSet, basename="leave-balances")
router.register("requests", LeaveRequestViewSet, basename="leave-requests")
router.register("approvals", LeaveApprovalViewSet, basename="leave-approvals")
router.register("attachments", LeaveAttachmentViewSet, basename="leave-attachments")
router.register("public-holidays", PublicHolidayViewSet, basename="public-holidays")

urlpatterns = [
    path(
        "requests/create/",
        CreateLeaveRequestView.as_view(),
        name="create-leave-request",
    ),
    path(
        "requests/<int:leave_request_id>/manager-approve/",
        ManagerApproveLeaveView.as_view(),
        name="manager-approve-leave",
    ),
    path(
        "requests/<int:leave_request_id>/hr-approve/",
        HRApproveLeaveView.as_view(),
        name="hr-approve-leave",
    ),
    path(
        "requests/<int:leave_request_id>/reject/",
        RejectLeaveView.as_view(),
        name="reject-leave",
    ),
    path("", include(router.urls)),
]
