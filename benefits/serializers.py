from rest_framework import serializers

from .models import (
    BenefitPlan,
    EmployeeBenefit,
    BenefitContributionHistory,
    EnrollmentWindow,
)


class BenefitPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenefitPlan
        fields = "__all__"


class EnrollmentWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentWindow
        fields = "__all__"


class EmployeeBenefitSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )

    benefit_name = serializers.CharField(
        source="benefit_plan.name",
        read_only=True,
    )

    class Meta:
        model = EmployeeBenefit
        fields = "__all__"


class BenefitContributionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BenefitContributionHistory
        fields = "__all__"


class EnrollBenefitSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()

    benefit_plan_id = serializers.IntegerField()

    enrollment_date = serializers.DateField()

    effective_date = serializers.DateField()

    end_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    employee_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    employer_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class BenefitApprovalSerializer(serializers.Serializer):
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
    )