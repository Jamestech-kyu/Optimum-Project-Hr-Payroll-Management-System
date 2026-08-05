from django.db.models import Sum
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
    processed_by_name = serializers.CharField(
        source="processed_by.full_name",
        read_only=True,
    )
    approved_by_name = serializers.CharField(
        source="approved_by.full_name",
        read_only=True,
    )
    pay_period = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    total_gross_pay = serializers.SerializerMethodField()
    total_deductions = serializers.SerializerMethodField()
    total_tax = serializers.SerializerMethodField()
    bank_payment_count = serializers.SerializerMethodField()
    bank_payment_status = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        fields = "__all__"

    def get_pay_period(self, obj):
        if obj.month and obj.year:
            return f"{obj.month}/{obj.year}"
        return None

    def get_employee_count(self, obj):
        return obj.payslips.count()

    def get_total_amount(self, obj):
        total = obj.payslips.aggregate(total=Sum("net_pay"))[
            "total"
        ]
        return total or 0

    def _payslip_totals(self, obj):
        return obj.payslips.aggregate(
            gross=Sum("gross_pay"),
            deductions=Sum("total_deductions"),
            tax=Sum("tax_amount"),
        )

    def get_total_gross_pay(self, obj):
        return self._payslip_totals(obj)["gross"] or 0

    def get_total_deductions(self, obj):
        return self._payslip_totals(obj)["deductions"] or 0

    def get_total_tax(self, obj):
        return self._payslip_totals(obj)["tax"] or 0

    def get_bank_payment_count(self, obj):
        return obj.bank_payments.count()

    def get_bank_payment_status(self, obj):
        statuses = list(
            obj.bank_payments.order_by().values_list("status", flat=True).distinct()
        )
        if not statuses:
            return "NOT_GENERATED"
        if "FAILED" in statuses:
            return "FAILED"
        if all(status == "PAID" for status in statuses):
            return "PAID"
        if "PROCESSING" in statuses:
            return "PROCESSING"
        return "PENDING"


class PayrollAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollAllowance
        fields = "__all__"


class PayrollDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDeduction
        fields = "__all__"


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )

    employee_email = serializers.CharField(
        source="employee.work_email",
        read_only=True,
    )

    department_name = serializers.CharField(
        source="employee.department.name",
        read_only=True,
    )

    designation_name = serializers.CharField(
        source="employee.designation.name",
        read_only=True,
    )

    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )
    reviewed_by_name = serializers.CharField(source="reviewed_by.full_name", read_only=True)

    payroll_month = serializers.IntegerField(
        source="payroll_run.month",
        read_only=True,
    )

    payroll_year = serializers.IntegerField(
        source="payroll_run.year",
        read_only=True,
    )

    payroll_status = serializers.CharField(
        source="payroll_run.status",
        read_only=True,
    )

    allowances = PayrollAllowanceSerializer(
        many=True,
        read_only=True,
    )

    deductions = PayrollDeductionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Payslip
        fields = [
            "id",
            "payroll_run",
            "payroll_month",
            "payroll_year",
            "payroll_status",
            "employee",
            "employee_name",
            "employee_email",
            "employee_number",
            "department_name",
            "designation_name",
            "basic_salary",
            "total_allowances",
            "gross_pay",
            "total_deductions",
            "tax_amount",
            "net_pay",
            "approval_status",
            "approval_comment",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "allowances",
            "deductions",
            "generated_at",
        ]


class BankPaymentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )

    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    class Meta:
        model = BankPayment
        fields = [
            "id",
            "payroll_run",
            "employee",
            "employee_name",
            "employee_number",
            "bank_name",
            "account_number",
            "account_name",
            "amount",
            "status",
            "created_at",
        ]


class PayComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayComponent
        fields = "__all__"

    def validate(self, data):
        calculation_type = data.get(
            "calculation_type",
            getattr(self.instance, "calculation_type", None),
        )

        default_amount = data.get(
            "default_amount",
            getattr(self.instance, "default_amount", None),
        )

        percentage_rate = data.get(
            "percentage_rate",
            getattr(self.instance, "percentage_rate", None),
        )

        errors = {}

        if (
            calculation_type == "FIXED"
            and default_amount is not None
            and default_amount < 0
        ):
            errors["default_amount"] = (
                "Default amount cannot be negative."
            )

        if calculation_type == "PERCENTAGE":
            if percentage_rate is None:
                errors["percentage_rate"] = (
                    "Percentage rate is required."
                )
            elif percentage_rate < 0:
                errors["percentage_rate"] = (
                    "Percentage rate cannot be negative."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class EmployeePayComponentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )

    component_name = serializers.CharField(
        source="component.name",
        read_only=True,
    )

    component_code = serializers.CharField(
        source="component.code",
        read_only=True,
    )

    component_type = serializers.CharField(
        source="component.component_type",
        read_only=True,
    )

    calculation_type = serializers.CharField(
        source="component.calculation_type",
        read_only=True,
    )

    class Meta:
        model = EmployeePayComponent
        fields = [
            "id",
            "employee",
            "employee_name",
            "component",
            "component_name",
            "component_code",
            "component_type",
            "calculation_type",
            "amount",
            "is_active",
        ]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Amount cannot be negative."
            )

        return value


class TaxBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxBand
        fields = "__all__"

    def validate(self, data):
        min_income = data.get(
            "min_income",
            getattr(self.instance, "min_income", None),
        )

        max_income = data.get(
            "max_income",
            getattr(self.instance, "max_income", None),
        )

        rate = data.get(
            "rate",
            getattr(self.instance, "rate", None),
        )

        errors = {}

        if min_income is not None and min_income < 0:
            errors["min_income"] = (
                "Minimum income cannot be negative."
            )

        if (
            min_income is not None
            and max_income is not None
            and max_income <= min_income
        ):
            errors["max_income"] = (
                "Maximum income must be greater than minimum income."
            )

        if rate is not None and (rate < 0 or rate > 100):
            errors["rate"] = (
                "Tax rate must be between 0 and 100."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class StatutoryRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutoryRate
        fields = "__all__"

    def validate(self, data):
        rate = data.get(
            "rate",
            getattr(self.instance, "rate", None),
        )

        is_percentage = data.get(
            "is_percentage",
            getattr(self.instance, "is_percentage", True),
        )

        if rate is not None and rate < 0:
            raise serializers.ValidationError({
                "rate": "Rate cannot be negative."
            })

        if is_percentage and rate is not None and rate > 100:
            raise serializers.ValidationError({
                "rate": (
                    "A percentage statutory rate cannot exceed 100."
                )
            })

        return data


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = "__all__"

    def validate(self, data):
        from_currency = data.get(
            "from_currency",
            getattr(self.instance, "from_currency", None),
        )

        to_currency = data.get(
            "to_currency",
            getattr(self.instance, "to_currency", None),
        )

        rate = data.get(
            "rate",
            getattr(self.instance, "rate", None),
        )

        errors = {}

        if (
            from_currency
            and to_currency
            and from_currency == to_currency
        ):
            errors["to_currency"] = (
                "Source and destination currencies must be different."
            )

        if rate is not None and rate <= 0:
            errors["rate"] = (
                "Exchange rate must be greater than zero."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class PayrollPolicySerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(
        source="currency.code",
        read_only=True,
    )

    class Meta:
        model = PayrollPolicy
        fields = [
            "id",
            "name",
            "working_days_per_month",
            "working_hours_per_day",
            "overtime_multiplier",
            "weekend_overtime_multiplier",
            "payroll_cutoff_day",
            "payslip_generation_day",
            "currency",
            "currency_code",
            "is_active",
        ]

    def validate(self, data):
        working_days = data.get(
            "working_days_per_month",
            getattr(
                self.instance,
                "working_days_per_month",
                None,
            ),
        )

        working_hours = data.get(
            "working_hours_per_day",
            getattr(
                self.instance,
                "working_hours_per_day",
                None,
            ),
        )

        cutoff_day = data.get(
            "payroll_cutoff_day",
            getattr(
                self.instance,
                "payroll_cutoff_day",
                None,
            ),
        )

        generation_day = data.get(
            "payslip_generation_day",
            getattr(
                self.instance,
                "payslip_generation_day",
                None,
            ),
        )

        errors = {}

        if working_days is not None and working_days <= 0:
            errors["working_days_per_month"] = (
                "Working days must be greater than zero."
            )

        if working_hours is not None and working_hours <= 0:
            errors["working_hours_per_day"] = (
                "Working hours must be greater than zero."
            )

        if cutoff_day is not None and not 1 <= cutoff_day <= 31:
            errors["payroll_cutoff_day"] = (
                "Payroll cutoff day must be between 1 and 31."
            )

        if (
            generation_day is not None
            and not 1 <= generation_day <= 31
        ):
            errors["payslip_generation_day"] = (
                "Payslip generation day must be between 1 and 31."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class GeneratePayrollSerializer(serializers.Serializer):
    month = serializers.IntegerField(
        min_value=1,
        max_value=12,
    )

    year = serializers.IntegerField(
        min_value=2024,
        max_value=2100,
    )

    employee_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
    )


class PayrollActionSerializer(serializers.Serializer):
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )


class PayrollCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=1000,
    )


class PayslipReviewSerializer(serializers.Serializer):
    payslip_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, data):
        if data["action"] == "REJECT" and not data.get("comment", "").strip():
            raise serializers.ValidationError({"comment": "A reason is required when rejecting payroll items."})
        return data


class BankReconciliationSerializer(serializers.Serializer):
    payment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    status = serializers.ChoiceField(choices=["PAID", "FAILED"])
