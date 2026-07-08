from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from audit.services import log_activity
from audit.utils import get_client_ip
from .models import *
from .serializers import *
from .services import generate_payroll_run
from accounts.permissions import RequiredPermission

from drf_spectacular.utils import extend_schema

from .models import *
from .serializers import *
from .services import generate_payroll_run


class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayrollAllowanceViewSet(viewsets.ModelViewSet):
    queryset = PayrollAllowance.objects.all()
    serializer_class = PayrollAllowanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayrollDeductionViewSet(viewsets.ModelViewSet):
    queryset = PayrollDeduction.objects.all()
    serializer_class = PayrollDeductionSerializer
    permission_classes = [permissions.IsAuthenticated]


class BankPaymentViewSet(viewsets.ModelViewSet):
    queryset = BankPayment.objects.all()
    serializer_class = BankPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayComponentViewSet(viewsets.ModelViewSet):
    queryset = PayComponent.objects.all()
    serializer_class = PayComponentSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmployeePayComponentViewSet(viewsets.ModelViewSet):
    queryset = EmployeePayComponent.objects.all()
    serializer_class = EmployeePayComponentSerializer
    permission_classes = [permissions.IsAuthenticated]


class TaxBandViewSet(viewsets.ModelViewSet):
    queryset = TaxBand.objects.all()
    serializer_class = TaxBandSerializer
    permission_classes = [permissions.IsAuthenticated]


class StatutoryRateViewSet(viewsets.ModelViewSet):
    queryset = StatutoryRate.objects.all()
    serializer_class = StatutoryRateSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]


class ExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayrollPolicyViewSet(viewsets.ModelViewSet):
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