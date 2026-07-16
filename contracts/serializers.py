from rest_framework import serializers

from .models import (
    EmploymentContract,
    ContractRenewal,
    ContractTermination,
)


def get_user_display_name(user):
    if not user:
        return None

    return (
        user.get_full_name()
        or user.username
        or user.email
    )


class EmploymentContractSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )

    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    created_by_name = serializers.SerializerMethodField()

    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmploymentContract
        fields = [
            "id",
            "employee",
            "employee_name",
            "employee_number",
            "contract_number",
            "contract_type",
            "start_date",
            "end_date",
            "probation_end_date",
            "basic_salary",
            "status",
            "terms",
            "document",
            "created_by",
            "created_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_by",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        instance = getattr(self, "instance", None)

        employee = data.get(
            "employee",
            getattr(instance, "employee", None),
        )

        contract_type = data.get(
            "contract_type",
            getattr(instance, "contract_type", None),
        )

        start_date = data.get(
            "start_date",
            getattr(instance, "start_date", None),
        )

        end_date = data.get(
            "end_date",
            getattr(instance, "end_date", None),
        )

        probation_end_date = data.get(
            "probation_end_date",
            getattr(instance, "probation_end_date", None),
        )

        basic_salary = data.get(
            "basic_salary",
            getattr(instance, "basic_salary", None),
        )

        status = data.get(
            "status",
            getattr(instance, "status", "DRAFT"),
        )

        errors = {}

        if start_date and end_date and end_date < start_date:
            errors["end_date"] = (
                "Contract end date cannot be before start date."
            )

        if (
            start_date
            and probation_end_date
            and probation_end_date < start_date
        ):
            errors["probation_end_date"] = (
                "Probation end date cannot be before contract start date."
            )

        if basic_salary is not None and basic_salary <= 0:
            errors["basic_salary"] = (
                "Contract salary must be greater than zero."
            )

        if (
            contract_type in [
                "FIXED_TERM",
                "INTERNSHIP",
                "CONSULTANCY",
            ]
            and not end_date
        ):
            errors["end_date"] = (
                "An end date is required for this contract type."
            )

        if (
            instance is None
            and employee
            and status == "ACTIVE"
            and EmploymentContract.objects.filter(
                employee=employee,
                status="ACTIVE",
            ).exists()
        ):
            errors["employee"] = (
                "This employee already has an active contract."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def get_created_by_name(self, obj):
        return get_user_display_name(obj.created_by)

    def get_approved_by_name(self, obj):
        return get_user_display_name(obj.approved_by)


class ContractRenewalSerializer(serializers.ModelSerializer):
    renewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ContractRenewal
        fields = [
            "id",
            "contract",
            "previous_end_date",
            "new_start_date",
            "new_end_date",
            "previous_salary",
            "new_salary",
            "reason",
            "renewed_by",
            "renewed_by_name",
            "renewed_at",
        ]

        read_only_fields = [
            "previous_end_date",
            "previous_salary",
            "renewed_by",
            "renewed_at",
        ]

    def validate(self, data):
        new_start_date = data.get("new_start_date")
        new_end_date = data.get("new_end_date")
        new_salary = data.get("new_salary")

        errors = {}

        if (
            new_start_date
            and new_end_date
            and new_end_date < new_start_date
        ):
            errors["new_end_date"] = (
                "New contract end date cannot be before new start date."
            )

        if new_salary is not None and new_salary <= 0:
            errors["new_salary"] = (
                "New salary must be greater than zero."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def get_renewed_by_name(self, obj):
        return get_user_display_name(obj.renewed_by)


class ContractTerminationSerializer(serializers.ModelSerializer):
    terminated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ContractTermination
        fields = [
            "id",
            "contract",
            "termination_type",
            "termination_date",
            "reason",
            "notice_period_days",
            "final_settlement_required",
            "terminated_by",
            "terminated_by_name",
            "created_at",
        ]

        read_only_fields = [
            "terminated_by",
            "created_at",
        ]

    def validate(self, data):
        contract = data.get(
            "contract",
            getattr(self.instance, "contract", None),
        )

        termination_date = data.get(
            "termination_date",
            getattr(self.instance, "termination_date", None),
        )

        if (
            contract
            and termination_date
            and termination_date < contract.start_date
        ):
            raise serializers.ValidationError({
                "termination_date": (
                    "Termination date cannot be before "
                    "the contract start date."
                )
            })

        return data

    def get_terminated_by_name(self, obj):
        return get_user_display_name(obj.terminated_by)


class ContractRenewActionSerializer(serializers.Serializer):
    new_start_date = serializers.DateField()
    new_end_date = serializers.DateField(
        required=False,
        allow_null=True,
    )
    new_salary = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )

    def validate(self, data):
        if (
            data.get("new_end_date")
            and data["new_end_date"] < data["new_start_date"]
        ):
            raise serializers.ValidationError({
                "new_end_date": (
                    "New end date cannot be before new start date."
                )
            })

        if data["new_salary"] <= 0:
            raise serializers.ValidationError({
                "new_salary": (
                    "New salary must be greater than zero."
                )
            })

        return data


class ContractTerminateActionSerializer(serializers.Serializer):
    termination_type = serializers.ChoiceField(
        choices=ContractTermination.TERMINATION_TYPE_CHOICES,
    )

    termination_date = serializers.DateField()

    reason = serializers.CharField(
        allow_blank=False,
        max_length=2000,
    )

    notice_period_days = serializers.IntegerField(
        min_value=0,
        default=0,
    )

    final_settlement_required = serializers.BooleanField(
        default=True,
    )
