from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FinalizeReviewView,
    HRApproveReviewView,
    ManagerApproveReviewView,
    PerformanceCycleViewSet,
    PerformanceGoalViewSet,
    PerformanceReviewViewSet,
    GoalProgressViewSet,
    SubmitPerformanceReviewView,
    SubmitGoalProgressView,
    EmployeeGoalsView,
)

router = DefaultRouter()

router.register(
    "cycles",
    PerformanceCycleViewSet,
    basename="performance-cycles",
)

router.register(
    "goals",
    PerformanceGoalViewSet,
    basename="performance-goals",
)

router.register(
    "reviews",
    PerformanceReviewViewSet,
    basename="performance-reviews",
)

router.register(
    "progress",
    GoalProgressViewSet,
    basename="goal-progress",
)

urlpatterns = [
    path(
        "submit-progress/",
        SubmitGoalProgressView.as_view(),
        name="submit-goal-progress",
    ),

    path(
        "employees/<int:employee_id>/goals/",
        EmployeeGoalsView.as_view(),
        name="employee-goals",
    ),

    path(
        "reviews/<int:review_id>/submit/",
        SubmitPerformanceReviewView.as_view(),
        name="submit-performance-review",
    ),

    path(
        "reviews/<int:review_id>/manager-approve/",
        ManagerApproveReviewView.as_view(),
        name="manager-approve-review",
    ),

    path(
        "reviews/<int:review_id>/hr-approve/",
        HRApproveReviewView.as_view(),
        name="hr-approve-review",
    ),

    path(
        "reviews/<int:review_id>/finalize/",
        FinalizeReviewView.as_view(),
        name="finalize-review",
    ),

    path("", include(router.urls)),
]
