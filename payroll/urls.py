from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PayrollRunViewSet,
    PayrollApprovalQueueView,
    PayrollHistoryView,
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
    PayslipReviewView,
    FinalizePayrollView,
    CancelPayrollView,
    DownloadPayslipView,
    ExportBankPaymentsView,
    ReconcileBankPaymentsView,
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
        "approval-queue/",
        PayrollApprovalQueueView.as_view(),
        name="payroll-approval-queue",
    ),
    path(
        "history/",
        PayrollHistoryView.as_view(),
        name="payroll-history",
    ),

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
        "runs/<int:payroll_run_id>/payslips/review/",
        PayslipReviewView.as_view(),
        name="review-payroll-payslips",
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
        "runs/<int:payroll_run_id>/bank-payments/export/",
        ExportBankPaymentsView.as_view(),
        name="export-bank-payments",
    ),
    path(
        "runs/<int:payroll_run_id>/bank-payments/reconcile/",
        ReconcileBankPaymentsView.as_view(),
        name="reconcile-bank-payments",
    ),
    path(
    "payslips/<int:payslip_id>/download/",
    DownloadPayslipView.as_view(),
    name="download-payslip",
),
]
