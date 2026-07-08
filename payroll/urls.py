from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()

router.register("runs", PayrollRunViewSet)
router.register("payslips", PayslipViewSet)
router.register("allowances", PayrollAllowanceViewSet)
router.register("deductions", PayrollDeductionViewSet)
router.register("bank-payments", BankPaymentViewSet)
router.register("components", PayComponentViewSet)
router.register("employee-components", EmployeePayComponentViewSet)
router.register("tax-bands", TaxBandViewSet)
router.register("statutory-rates", StatutoryRateViewSet)
router.register("currencies", CurrencyViewSet)
router.register("exchange-rates", ExchangeRateViewSet)
router.register("policies", PayrollPolicyViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("generate/", GeneratePayrollView.as_view(), name="generate-payroll"),
]