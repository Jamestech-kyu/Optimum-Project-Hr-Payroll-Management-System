from rest_framework import serializers

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


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = "__all__"


class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = "__all__"


class PayrollAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollAllowance
        fields = "__all__"


class PayrollDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDeduction
        fields = "__all__"


class BankPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankPayment
        fields = "__all__"


class PayComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayComponent
        fields = "__all__"


class EmployeePayComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePayComponent
        fields = "__all__"


class TaxBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxBand
        fields = "__all__"


class StatutoryRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutoryRate
        fields = "__all__"


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = "__all__"


class PayrollPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPolicy
        fields = "__all__"


class GeneratePayrollSerializer(serializers.Serializer):
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2024, max_value=2100)