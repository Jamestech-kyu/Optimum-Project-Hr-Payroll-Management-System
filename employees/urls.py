from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmployeeViewSet,
    EmployeeDocumentViewSet,
    EmployeeEducationViewSet,
    EmployeeWorkExperienceViewSet,
    EmployeeDependantViewSet,
    EmployeeCertificationViewSet,
    EmployeeSkillViewSet,
    EmployeeBankAccountViewSet,
    EmployeeAssetViewSet,
    EmployeeFinancialProfileView,
    EmployeeSalaryHistoryView,
    EmployeeSalaryAdjustmentView,
)

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employees")
router.register("documents", EmployeeDocumentViewSet, basename="employee-documents")
router.register("education", EmployeeEducationViewSet, basename="employee-education")
router.register("work-experience", EmployeeWorkExperienceViewSet, basename="employee-work-experience")
router.register("dependants", EmployeeDependantViewSet, basename="employee-dependants")
router.register("certifications", EmployeeCertificationViewSet, basename="employee-certifications")
router.register("skills", EmployeeSkillViewSet, basename="employee-skills")
router.register("bank-accounts", EmployeeBankAccountViewSet, basename="employee-bank-accounts")
router.register("assets", EmployeeAssetViewSet, basename="employee-assets")

urlpatterns = [
    path(
        "employees/<int:employee_id>/financial-profile/",
        EmployeeFinancialProfileView.as_view(),
        name="employee-financial-profile",
    ),
    path(
        "employees/<int:employee_id>/salary-history/",
        EmployeeSalaryHistoryView.as_view(),
        name="employee-salary-history",
    ),
    path(
        "employees/<int:employee_id>/salary-adjustment/",
        EmployeeSalaryAdjustmentView.as_view(),
        name="employee-salary-adjustment",
    ),
    path("", include(router.urls)),
]
