from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BenefitPlanViewSet,
    EnrollmentWindowViewSet,
    EmployeeBenefitViewSet,
    BenefitContributionHistoryViewSet,
    EnrollEmployeeBenefitView,
    EmployeeBenefitsView,
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
        "employees/<int:employee_id>/benefits/",
        EmployeeBenefitsView.as_view(),
        name="employee-benefits",
    ),

    path("", include(router.urls)),
]