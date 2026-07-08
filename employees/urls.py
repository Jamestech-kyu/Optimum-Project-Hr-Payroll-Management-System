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
    path("", include(router.urls)),
]