from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PayrollRunViewSet,
    PayslipViewSet,
    PayrollAllowanceViewSet,
    PayrollDeductionViewSet,
    BankPaymentViewSet,
    PayComponentViewSet,
    EmployeePayComponentViewSet,
    TaxBandViewSet,
    StatutoryRateViewSet,
    CurrencyViewSet,
    ExchangeRateViewSet,
    PayrollPolicyViewSet,
    GeneratePayrollView,
    SubmitPayrollView,
    ApprovePayrollView,
    FinalizePayrollView,
    CancelPayrollView,
    DownloadPayslipView,
)

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

    path(
        "generate/",
        GeneratePayrollView.as_view(),
        name="generate-payroll",
    ),

    path(
        "runs/<int:payroll_run_id>/submit/",
        SubmitPayrollView.as_view(),
        name="submit-payroll",
    ),

    path(
        "runs/<int:payroll_run_id>/approve/",
        ApprovePayrollView.as_view(),
        name="approve-payroll",
    ),

    path(
        "runs/<int:payroll_run_id>/finalize/",
        FinalizePayrollView.as_view(),
        name="finalize-payroll",
    ),

    path(
        "runs/<int:payroll_run_id>/cancel/",
        CancelPayrollView.as_view(),
        name="cancel-payroll",
    ),
    path(
    "payslips/<int:payslip_id>/download/",
    DownloadPayslipView.as_view(),
    name="download-payslip",
),
]
