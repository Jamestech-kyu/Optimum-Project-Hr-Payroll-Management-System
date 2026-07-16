from rest_framework import serializers

from .models import (
    BankDisbursement,
    DeductionType,
    Payslip,
    Payroll,
    PayrollDeduction,
    PayrollRun,
    SalaryStructure,
    TaxSlab,
)


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'


class TaxSlabSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSlab
        fields = '__all__'


class DeductionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeductionType
        fields = '__all__'


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'


class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = '__all__'


class PayrollDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDeduction
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = '__all__'


class BankDisbursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDisbursement
        fields = '__all__'

