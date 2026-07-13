from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, DepartmentViewSet, DesignationViewSet

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branches")
router.register("departments", DepartmentViewSet, basename="departments")
router.register("designations", DesignationViewSet, basename="designations")

urlpatterns = [
    path("", include(router.urls)),
]