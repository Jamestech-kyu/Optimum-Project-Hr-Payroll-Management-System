from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AcceptTrainingRecommendationView,
    ApproveTrainingEnrollmentView,
    DeclineTrainingRecommendationView,
    EnrollEmployeeTrainingView,
    RecordTrainingAssessmentView,
    RecordTrainingAttendanceView,
    RecommendTrainingView,
    RejectTrainingEnrollmentView,
    TrainingAssessmentViewSet,
    TrainingAttendanceViewSet,
    TrainingCategoryViewSet,
    TrainingCertificateViewSet,
    TrainingCourseViewSet,
    TrainingEnrollmentViewSet,
    TrainingRecommendationViewSet,
    TrainingSessionViewSet,
)

router = DefaultRouter()

router.register(
    "categories",
    TrainingCategoryViewSet,
    basename="training-categories",
)
router.register(
    "courses",
    TrainingCourseViewSet,
    basename="training-courses",
)
router.register(
    "sessions",
    TrainingSessionViewSet,
    basename="training-sessions",
)
router.register(
    "enrollments",
    TrainingEnrollmentViewSet,
    basename="training-enrollments",
)
router.register(
    "attendance",
    TrainingAttendanceViewSet,
    basename="training-attendance",
)
router.register(
    "assessments",
    TrainingAssessmentViewSet,
    basename="training-assessments",
)
router.register(
    "certificates",
    TrainingCertificateViewSet,
    basename="training-certificates",
)
router.register(
    "recommendations",
    TrainingRecommendationViewSet,
    basename="training-recommendations",
)

urlpatterns = [
    path(
        "enroll/",
        EnrollEmployeeTrainingView.as_view(),
        name="training-enroll",
    ),
    path(
        "enrollments/<int:enrollment_id>/approve/",
        ApproveTrainingEnrollmentView.as_view(),
        name="training-enrollment-approve",
    ),
    path(
        "enrollments/<int:enrollment_id>/reject/",
        RejectTrainingEnrollmentView.as_view(),
        name="training-enrollment-reject",
    ),
    path(
        "attendance/",
        RecordTrainingAttendanceView.as_view(),
        name="training-attendance-record",
    ),
    path(
        "assessment/",
        RecordTrainingAssessmentView.as_view(),
        name="training-assessment-record",
    ),
    path(
        "recommend/",
        RecommendTrainingView.as_view(),
        name="training-recommend",
    ),
    path(
        "recommendations/<int:recommendation_id>/accept/",
        AcceptTrainingRecommendationView.as_view(),
        name="training-recommendation-accept",
    ),
    path(
        "recommendations/<int:recommendation_id>/decline/",
        DeclineTrainingRecommendationView.as_view(),
        name="training-recommendation-decline",
    ),
    path("", include(router.urls)),
]
