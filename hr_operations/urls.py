from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PerformanceReviewViewSet,
    PerformanceGoalViewSet,
    DisciplinaryCaseViewSet,
    AnnouncementViewSet,
    TrainingViewSet,
    TrainingEnrollmentViewSet,
)

router = DefaultRouter()
router.register(r"performance-reviews", PerformanceReviewViewSet, basename="performance-review")
router.register(r"performance-goals", PerformanceGoalViewSet, basename="performance-goal")
router.register(r"disciplinary-cases", DisciplinaryCaseViewSet, basename="disciplinary-case")
router.register(r"announcements", AnnouncementViewSet, basename="announcement")
router.register(r"trainings", TrainingViewSet, basename="training")
router.register(r"training-enrollments", TrainingEnrollmentViewSet, basename="training-enrollment")

urlpatterns = [
    path("", include(router.urls)),
]