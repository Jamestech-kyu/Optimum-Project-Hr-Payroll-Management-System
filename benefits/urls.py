from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ApproveEmployeeBenefitView,
    BenefitPlanViewSet,
    EnrollmentWindowViewSet,
    EmployeeBenefitViewSet,
    BenefitContributionHistoryViewSet,
    EnrollEmployeeBenefitView,
    EmployeeBenefitsView,
    RejectEmployeeBenefitView,
)

router = DefaultRouter()

router.register(
    "plans",
    BenefitPlanViewSet,
    basename="benefit-plans",
)

router.register(
    "enrollments",
    EmployeeBenefitViewSet,
    basename="benefit-enrollments",
)

router.register(
    "windows",
    EnrollmentWindowViewSet,
    basename="benefit-windows",
)

router.register(
    "contributions",
    BenefitContributionHistoryViewSet,
    basename="benefit-contributions",
)

urlpatterns = [
    path(
        "enroll/",
        EnrollEmployeeBenefitView.as_view(),
        name="benefit-enroll",
    ),

    path(
        "enrollments/<int:enrollment_id>/approve/",
        ApproveEmployeeBenefitView.as_view(),
        name="benefit-enrollment-approve",
    ),

    path(
        "enrollments/<int:enrollment_id>/reject/",
        RejectEmployeeBenefitView.as_view(),
        name="benefit-enrollment-reject",
    ),

    path(
        "employees/<int:employee_id>/benefits/",
        EmployeeBenefitsView.as_view(),
        name="employee-benefits",
    ),

    path("", include(router.urls)),
]
