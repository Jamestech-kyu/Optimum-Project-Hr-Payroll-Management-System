from rest_framework import filters, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend

from .pdf_utils import generate_payslip_pdf
from accounts.object_permissions import (
    check_related_employee_permission,
)
from accounts.permissions import RequiredPermission
from audit.mixins import AuditViewSetMixin
from .models import (
    PayrollRun,
    Payslip,
    PayrollAllowance,
    PayrollDeduction,
    BankPayment,
    PayComponent,
    EmployeePayComponent,
    TaxBand,
    StatutoryRate,
    Currency,
    ExchangeRate,
    PayrollPolicy,
)
from .serializers import (
    PayrollRunSerializer,
    PayslipSerializer,
    PayrollAllowanceSerializer,
    PayrollDeductionSerializer,
    BankPaymentSerializer,
    PayComponentSerializer,
    EmployeePayComponentSerializer,
    TaxBandSerializer,
    StatutoryRateSerializer,
    CurrencySerializer,
    ExchangeRateSerializer,
    PayrollPolicySerializer,
    GeneratePayrollSerializer,
    PayrollActionSerializer,
    PayrollCancelSerializer,
)
from .services import (
    generate_payroll_run,
    submit_payroll_for_approval,
    approve_payroll_run,
    finalize_payroll_run,
    cancel_payroll_run,
)

class PayrollRunViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayslipViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = Payslip.objects.select_related(
        "employee",
        "payroll_run",
    )
    serializer_class = PayslipSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
    ]
    ordering_fields = "__all__"
    ordering = ["-generated_at"]
    filterset_fields = [
        "employee",
        "payroll_run",
    ]

    def get_object(self):
        return check_related_employee_permission(
            user=self.request.user,
            queryset=Payslip.objects.select_related(
                "employee",
            ),
            employee_field="employee",
            object_id=self.kwargs["pk"],
            permission_codename="payroll.view",
        )


class PayrollAllowanceViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayrollAllowance.objects.all()
    serializer_class = PayrollAllowanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayrollDeductionViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayrollDeduction.objects.all()
    serializer_class = PayrollDeductionSerializer
    permission_classes = [permissions.IsAuthenticated]


class BankPaymentViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = BankPayment.objects.all()
    serializer_class = BankPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayComponentViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayComponent.objects.all()
    serializer_class = PayComponentSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmployeePayComponentViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = EmployeePayComponent.objects.all()
    serializer_class = EmployeePayComponentSerializer
    permission_classes = [permissions.IsAuthenticated]


class TaxBandViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = TaxBand.objects.all()
    serializer_class = TaxBandSerializer
    permission_classes = [permissions.IsAuthenticated]


class StatutoryRateViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = StatutoryRate.objects.all()
    serializer_class = StatutoryRateSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrencyViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]


class ExchangeRateViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayrollPolicyViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayrollPolicy.objects.all()
    serializer_class = PayrollPolicySerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    request=GeneratePayrollSerializer,
    responses={201: PayrollRunSerializer},
    tags=["Payroll Engine"],
)
class GeneratePayrollView(APIView):
    permission_classes = [RequiredPermission("payroll.generate")]

    def post(self, request):
        serializer = GeneratePayrollSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payroll_run = generate_payroll_run(
            month=serializer.validated_data["month"],
            year=serializer.validated_data["year"],
            processed_by=request.user,
            request=request,
        )

        return Response(
            {
                "message": "Payroll generated successfully.",
                "payroll": PayrollRunSerializer(payroll_run).data,
            },
            status=status.HTTP_201_CREATED,
        )
@extend_schema(
    request=PayrollActionSerializer,
    responses={200: PayrollRunSerializer},
    tags=["Payroll Workflow"],
)
class SubmitPayrollView(APIView):
    permission_classes = [
        RequiredPermission("payroll.generate")
    ]

    def post(self, request, payroll_run_id):
        serializer = PayrollActionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            payroll_run = PayrollRun.objects.get(
                id=payroll_run_id
            )

            payroll_run = submit_payroll_for_approval(
                payroll_run=payroll_run,
                submitted_by=request.user,
                comment=serializer.validated_data.get(
                    "comment",
                    "",
                ),
                request=request,
            )

            return Response(
                {
                    "message": (
                        "Payroll submitted for approval."
                    ),
                    "payroll": PayrollRunSerializer(
                        payroll_run
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        except PayrollRun.DoesNotExist:
            return Response(
                {"message": "Payroll run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    request=PayrollActionSerializer,
    responses={200: PayrollRunSerializer},
    tags=["Payroll Workflow"],
)
class ApprovePayrollView(APIView):
    permission_classes = [
        RequiredPermission("payroll.approve")
    ]

    def post(self, request, payroll_run_id):
        serializer = PayrollActionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            payroll_run = PayrollRun.objects.get(
                id=payroll_run_id
            )

            payroll_run = approve_payroll_run(
                payroll_run=payroll_run,
                approved_by=request.user,
                comment=serializer.validated_data.get(
                    "comment",
                    "",
                ),
                request=request,
            )

            return Response(
                {
                    "message": "Payroll approved.",
                    "payroll": PayrollRunSerializer(
                        payroll_run
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        except PayrollRun.DoesNotExist:
            return Response(
                {"message": "Payroll run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    request=PayrollActionSerializer,
    responses={200: PayrollRunSerializer},
    tags=["Payroll Workflow"],
)
class FinalizePayrollView(APIView):
    permission_classes = [
        RequiredPermission("payroll.approve")
    ]

    def post(self, request, payroll_run_id):
        serializer = PayrollActionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            payroll_run = PayrollRun.objects.get(
                id=payroll_run_id
            )

            payroll_run = finalize_payroll_run(
                payroll_run=payroll_run,
                finalized_by=request.user,
                comment=serializer.validated_data.get(
                    "comment",
                    "",
                ),
                request=request,
            )

            return Response(
                {
                    "message": (
                        "Payroll finalized and locked."
                    ),
                    "payroll": PayrollRunSerializer(
                        payroll_run
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        except PayrollRun.DoesNotExist:
            return Response(
                {"message": "Payroll run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    request=PayrollCancelSerializer,
    responses={200: PayrollRunSerializer},
    tags=["Payroll Workflow"],
)
class CancelPayrollView(APIView):
    permission_classes = [
        RequiredPermission("payroll.approve")
    ]

    def post(self, request, payroll_run_id):
        serializer = PayrollCancelSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            payroll_run = PayrollRun.objects.get(
                id=payroll_run_id
            )

            payroll_run = cancel_payroll_run(
                payroll_run=payroll_run,
                cancelled_by=request.user,
                reason=serializer.validated_data[
                    "reason"
                ],
                request=request,
            )

            return Response(
                {
                    "message": "Payroll cancelled.",
                    "payroll": PayrollRunSerializer(
                        payroll_run
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        except PayrollRun.DoesNotExist:
            return Response(
                {"message": "Payroll run not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
@extend_schema(
    responses={(200, "application/pdf"): bytes},
    tags=["Payroll Payslips"],
)
class DownloadPayslipView(APIView):
    permission_classes = [
        RequiredPermission("payroll.view")
    ]

    def get(self, request, payslip_id):
        try:
            payslip = (
                Payslip.objects
                .select_related(
                    "employee",
                    "employee__branch",
                    "employee__department",
                    "employee__designation",
                    "payroll_run",
                )
                .prefetch_related(
                    "allowances",
                    "deductions",
                )
                .get(id=payslip_id)
            )

        except Payslip.DoesNotExist:
            return Response(
                {"message": "Payslip not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payslip.payroll_run.status not in [
            "APPROVED",
            "FINALIZED",
        ]:
            return Response(
                {
                    "message": (
                        "Payslip can only be downloaded after "
                        "payroll approval."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        pdf_buffer = generate_payslip_pdf(payslip)

        filename = (
            f"payslip_"
            f"{payslip.employee.employee_number}_"
            f"{payslip.payroll_run.year}_"
            f"{payslip.payroll_run.month:02d}.pdf"
        )

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )
