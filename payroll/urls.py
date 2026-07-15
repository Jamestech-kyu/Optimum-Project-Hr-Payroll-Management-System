from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PayrollRunViewSet, PayrollViewSet, PayrollDeductionViewSet

router = DefaultRouter()
router.register(r'payroll-runs', PayrollRunViewSet, basename='payroll-runs')
router.register(r'', PayrollViewSet, basename='payroll')
router.register(r'deductions', PayrollDeductionViewSet, basename='payroll-deductions')

urlpatterns = [
    path('', include(router.urls)),
]

