from rest_framework import filters, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .pdf_utils import generate_payslip_pdf
from accounts.object_permissions import (
    check_related_employee_permission,
)
from accounts.permissions import RequiredPermission
from accounts.scopes import scope_related_employee_queryset
from audit.mixins import AuditViewSetMixin
from audit.models import AuditLog
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
    PayslipReviewSerializer,
    PayrollCancelSerializer,
    BankReconciliationSerializer,
)
from .services import (
    generate_payroll_run,
    submit_payroll_for_approval,
    approve_payroll_run,
    review_payslips,
    finalize_payroll_run,
    cancel_payroll_run,
)

class PayrollRunViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayrollRun.objects.select_related(
        "processed_by",
        "approved_by",
    ).all()
    serializer_class = PayrollRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["month", "year", "status"]
    ordering_fields = ["month", "year", "status", "created_at", "processed_at", "approved_at"]


class PayslipViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = Payslip.objects.select_related(
        "employee",
        "payroll_run",
        "employee__department",
        "employee__designation",
    )
    serializer_class = PayslipSerializer
    permission_classes = [RequiredPermission("payroll.view")]
    http_method_names = ["get", "head", "options"]
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

    def get_queryset(self):
        # Payslips carry salary data, so rows are restricted to the caller's
        # data scope: EMPLOYEE holds payroll.view at OWN scope and therefore
        # sees only their own, while HR and payroll roles hold it organisation
        # wide.
        return scope_related_employee_queryset(
            user=self.request.user,
            queryset=super().get_queryset(),
            employee_field="employee",
            permission_codename="payroll.view",
        )

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
    http_method_names = ["get", "head", "options"]


class PayrollDeductionViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = PayrollDeduction.objects.all()
    serializer_class = PayrollDeductionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "head", "options"]


class BankPaymentViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PAYROLL"

    queryset = BankPayment.objects.select_related("employee", "payroll_run").all()
    serializer_class = BankPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["payroll_run", "status", "employee"]
    ordering_fields = ["created_at", "amount", "status"]


class PayrollApprovalQueueView(APIView):
    permission_classes = [RequiredPermission("payroll.approve")]

    def get(self, request):
        runs = (
            PayrollRun.objects.filter(status__in=["PENDING_APPROVAL", "APPROVED", "FINALIZED"])
            .select_related("processed_by", "approved_by")
            .prefetch_related(
                "payslips__employee__department",
                "payslips__employee__designation",
                "payslips__reviewed_by",
            )
            .order_by("-created_at")
        )
        return Response({
            "results": [
                {
                    "run": PayrollRunSerializer(run, context={"request": request}).data,
                    "payslips": PayslipSerializer(
                        run.payslips.all(), many=True, context={"request": request}
                    ).data,
                }
                for run in runs
            ]
        })


class PayrollHistoryView(APIView):
    permission_classes = [RequiredPermission("payroll.view")]

    def get(self, request):
        runs = (
            PayrollRun.objects.select_related("processed_by", "approved_by")
            .prefetch_related(
                "payslips__employee__department",
                "payslips__employee__designation",
                "payslips__reviewed_by",
                "bank_payments",
            )
            .order_by("-created_at")
        )
        records = []
        for run in runs:
            audit_entries = AuditLog.objects.filter(
                module__iexact="Payroll", object_id=str(run.id)
            ).select_related("user").order_by("created_at")
            history = [
                {
                    "id": entry.id,
                    "action": entry.description or entry.get_action_display(),
                    "date": entry.created_at,
                    "user": (
                        entry.user.get_full_name()
                        or getattr(entry.user, "full_name", "")
                        or entry.user.username
                    ) if entry.user else "System",
                    "note": entry.description,
                }
                for entry in audit_entries
            ]
            records.append({
                "run": PayrollRunSerializer(run, context={"request": request}).data,
                "payslips": PayslipSerializer(run.payslips.all(), many=True, context={"request": request}).data,
                "bank_payments": BankPaymentSerializer(run.bank_payments.all(), many=True, context={"request": request}).data,
                "history": history,
            })
        return Response({"results": records})


@extend_schema(tags=["Payroll Bank Integration"])
class ExportBankPaymentsView(APIView):
    permission_classes = [RequiredPermission("payroll.approve")]

    def get(self, request, payroll_run_id):
        try:
            payroll_run = PayrollRun.objects.get(id=payroll_run_id)
        except PayrollRun.DoesNotExist:
            return Response({"message": "Payroll run not found."}, status=404)

        if payroll_run.status not in ["APPROVED", "FINALIZED"]:
            return Response(
                {"message": "Approve the payroll before exporting bank instructions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payments = payroll_run.bank_payments.exclude(status="FAILED").select_related("employee")
        if not payments.exists():
            return Response(
                {"message": "No eligible bank payments found for this payroll run."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invalid_payments = payments.filter(account_number="")
        if invalid_payments.exists():
            return Response(
                {"message": "Bank instruction export is blocked by missing account numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payroll_run.status == "APPROVED":
            payments.filter(status="PENDING").update(status="PROCESSING")

        lines = ["payment_id,employee_number,employee_name,bank_name,account_number,account_name,amount,reference"]
        for payment in payments:
            lines.append(
                ",".join([
                    str(payment.id),
                    payment.employee.employee_number,
                    f'"{payment.employee.full_name.replace("\"", "\"\"")}"',
                    f'"{payment.bank_name.replace("\"", "\"\"")}"',
                    payment.account_number,
                    f'"{payment.account_name.replace("\"", "\"\"")}"',
                    str(payment.amount),
                    f"PAY-{payroll_run.year}{payroll_run.month:02d}-{payment.id}",
                ])
            )

        response = HttpResponse("\n".join(lines), content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="payroll_{payroll_run.year}_{payroll_run.month:02d}_bank_instructions.csv"'
        )
        return response


@extend_schema(
    request=BankReconciliationSerializer,
    tags=["Payroll Bank Integration"],
)
class ReconcileBankPaymentsView(APIView):
    permission_classes = [RequiredPermission("payroll.approve")]

    def post(self, request, payroll_run_id):
        serializer = BankReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payroll_run = PayrollRun.objects.get(id=payroll_run_id)
        except PayrollRun.DoesNotExist:
            return Response({"message": "Payroll run not found."}, status=404)

        if payroll_run.status not in ["APPROVED", "FINALIZED"]:
            return Response(
                {"message": "Only approved payroll bank payments can be reconciled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payments = payroll_run.bank_payments.filter(
            id__in=serializer.validated_data["payment_ids"]
        )
        if payments.count() != len(set(serializer.validated_data["payment_ids"])):
            return Response(
                {"message": "One or more payments do not belong to this payroll run."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payments.update(status=serializer.validated_data["status"])
        if (
            serializer.validated_data["status"] == "PAID"
            and not payroll_run.bank_payments.exclude(status="PAID").exists()
        ):
            payroll_run.status = "FINALIZED"
            payroll_run.save(update_fields=["status"])

        return Response(
            {
                "message": "Bank payments reconciled successfully.",
                "updated": payments.count(),
                "payroll_status": payroll_run.status,
                "reconciled_at": timezone.now(),
            }
        )


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
            employee_ids=serializer.validated_data.get("employee_ids"),
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
    request=PayslipReviewSerializer,
    responses={200: PayslipSerializer(many=True)},
    tags=["Payroll Workflow"],
)
class PayslipReviewView(APIView):
    permission_classes = [RequiredPermission("payroll.approve")]

    def post(self, request, payroll_run_id):
        serializer = PayslipReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payroll_run = PayrollRun.objects.get(id=payroll_run_id)
            payslips = review_payslips(
                payroll_run=payroll_run,
                payslip_ids=serializer.validated_data["payslip_ids"],
                action=serializer.validated_data["action"],
                reviewed_by=request.user,
                comment=serializer.validated_data.get("comment", ""),
                request=request,
            )
            return Response({
                "message": "Payroll items reviewed.",
                "payslips": PayslipSerializer(payslips, many=True).data,
            })
        except PayrollRun.DoesNotExist:
            return Response({"message": "Payroll run not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as error:
            return Response({"message": str(error)}, status=status.HTTP_400_BAD_REQUEST)


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
