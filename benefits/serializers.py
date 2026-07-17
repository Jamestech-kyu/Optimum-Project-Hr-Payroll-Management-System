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
    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    benefit_name = serializers.CharField(
        source="benefit_plan.name",
        read_only=True,
    )

    benefit_code = serializers.CharField(
        source="benefit_plan.code",
        read_only=True,
    )

    benefit_type = serializers.CharField(
        source="benefit_plan.benefit_type",
        read_only=True,
    )

    created_by_name = serializers.CharField(
        source="created_by.get_full_name",
        read_only=True,
    )

    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = EmployeeBenefit
        fields = "__all__"
        read_only_fields = [
            "status",
            "created_by",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def get_employee_name(self, obj):
        if hasattr(obj.employee, "full_name"):
            full_name = obj.employee.full_name

            if callable(full_name):
                return full_name()

            return full_name

        return str(obj.employee)


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
        required=False,
        default=0,
        min_value=0,
    )

    employer_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=0,
        min_value=0,
    )

    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, data):
        effective_date = data["effective_date"]
        enrollment_date = data["enrollment_date"]
        end_date = data.get("end_date")

        if effective_date < enrollment_date:
            raise serializers.ValidationError(
                {
                    "effective_date": (
                        "Effective date cannot be earlier than "
                        "the enrollment date."
                    )
                }
            )

        if end_date and end_date < effective_date:
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "End date cannot be earlier than "
                        "the effective date."
                    )
                }
            )

        return data
    


class BenefitApprovalSerializer(serializers.Serializer):
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
    )