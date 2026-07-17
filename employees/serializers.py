from rest_framework import serializers

from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeWorkExperience,
    EmployeeDependant,
    EmployeeCertification,
    EmployeeSkill,
    EmployeeBankAccount,
    EmployeeAsset,
    SalaryHistory,
)


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = "__all__"

    def validate(self, data):
        instance = getattr(self, "instance", None)
        errors = {}

        hire_date = data.get(
            "hire_date",
            getattr(instance, "hire_date", None),
        )

        confirmation_date = data.get(
            "confirmation_date",
            getattr(instance, "confirmation_date", None),
        )

        probation_end_date = data.get(
            "probation_end_date",
            getattr(instance, "probation_end_date", None),
        )

        basic_salary = data.get(
            "basic_salary",
            getattr(instance, "basic_salary", None),
        )

        branch = data.get(
            "branch",
            getattr(instance, "branch", None),
        )

        department = data.get(
            "department",
            getattr(instance, "department", None),
        )

        designation = data.get(
            "designation",
            getattr(instance, "designation", None),
        )

        # Require organization fields only when creating a new employee.
        if instance is None:
            if not branch:
                errors["branch"] = "Branch is required."

            if not department:
                errors["department"] = "Department is required."

            if not designation:
                errors["designation"] = "Designation is required."

            if basic_salary is None or basic_salary <= 0:
                errors["basic_salary"] = (
                    "Basic salary must be greater than zero."
                )

        # Prevent explicitly clearing organization fields during updates.
        if instance is not None:
            if "branch" in data and data["branch"] is None:
                errors["branch"] = "Branch cannot be cleared."

            if "department" in data and data["department"] is None:
                errors["department"] = "Department cannot be cleared."

            if "designation" in data and data["designation"] is None:
                errors["designation"] = "Designation cannot be cleared."

            if "basic_salary" in data and data["basic_salary"] <= 0:
                errors["basic_salary"] = (
                    "Basic salary must be greater than zero."
                )

        if (
            hire_date
            and confirmation_date
            and confirmation_date < hire_date
        ):
            errors["confirmation_date"] = (
                "Confirmation date cannot be before hire date."
            )

        if (
            hire_date
            and probation_end_date
            and probation_end_date < hire_date
        ):
            errors["probation_end_date"] = (
                "Probation end date cannot be before hire date."
            )

        # Ensure department belongs to the selected branch.
        if (
            branch
            and department
            and hasattr(department, "branch_id")
            and department.branch_id
            and department.branch_id != branch.id
        ):
            errors["department"] = (
                "The selected department does not belong to "
                "the selected branch."
            )

        # Ensure designation belongs to the selected department.
        if (
            department
            and designation
            and hasattr(designation, "department_id")
            and designation.department_id
            and designation.department_id != department.id
        ):
            errors["designation"] = (
                "The selected designation does not belong to "
                "the selected department."
            )

        manager = data.get(
            "manager",
            getattr(instance, "manager", None),
        )

        if instance and manager and manager.id == instance.id:
            errors["manager"] = (
                "An employee cannot be assigned as their own manager."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = "__all__"


class EmployeeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEducation
        fields = "__all__"

    def validate(self, data):
        start_date = data.get(
            "start_date",
            getattr(self.instance, "start_date", None),
        )

        end_date = data.get(
            "end_date",
            getattr(self.instance, "end_date", None),
        )

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": (
                    "Education end date cannot be before start date."
                )
            })

        return data


class EmployeeWorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeWorkExperience
        fields = "__all__"

    def validate(self, data):
        start_date = data.get(
            "start_date",
            getattr(self.instance, "start_date", None),
        )

        end_date = data.get(
            "end_date",
            getattr(self.instance, "end_date", None),
        )

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": (
                    "Work experience end date cannot be before start date."
                )
            })

        return data


class EmployeeDependantSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDependant
        fields = "__all__"


class EmployeeCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCertification
        fields = "__all__"

    def validate(self, data):
        issue_date = data.get(
            "issue_date",
            getattr(self.instance, "issue_date", None),
        )

        expiry_date = data.get(
            "expiry_date",
            getattr(self.instance, "expiry_date", None),
        )

        if issue_date and expiry_date and expiry_date < issue_date:
            raise serializers.ValidationError({
                "expiry_date": (
                    "Certification expiry date cannot be "
                    "before issue date."
                )
            })

        return data


class EmployeeSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkill
        fields = "__all__"


class EmployeeBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankAccount
        fields = "__all__"

    def validate(self, data):
        account_number = data.get(
            "account_number",
            getattr(self.instance, "account_number", ""),
        )

        account_name = data.get(
            "account_name",
            getattr(self.instance, "account_name", ""),
        )

        bank_name = data.get(
            "bank_name",
            getattr(self.instance, "bank_name", ""),
        )

        errors = {}

        if not bank_name:
            errors["bank_name"] = "Bank name is required."

        if not account_name:
            errors["account_name"] = "Account name is required."

        if not account_number:
            errors["account_number"] = (
                "Bank account number is required."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class EmployeeAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAsset
        fields = "__all__"
class SalaryHistorySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )

    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SalaryHistory
        fields = [
            "id",
            "employee",
            "employee_name",
            "employee_number",
            "previous_salary",
            "new_salary",
            "adjustment_type",
            "effective_date",
            "reason",
            "changed_by",
            "changed_by_name",
            "created_at",
        ]

        read_only_fields = [
            "employee",
            "previous_salary",
            "changed_by",
            "created_at",
        ]

    def get_changed_by_name(self, obj):
        if not obj.changed_by:
            return None

        return (
            obj.changed_by.get_full_name()
            or obj.changed_by.username
            or obj.changed_by.email
        )


class FinancialProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_number",
            "full_name",
            "basic_salary",
            "house_allowance",
            "transport_allowance",
            "medical_allowance",
            "other_allowance",
            "gross_salary",
            "bank_name",
            "bank_branch",
            "bank_account_number",
            "bank_account_name",
            "swift_code",
            "tax_pin",
            "social_security_number",
            "health_insurance_number",
        ]

    def validate(self, data):
        errors = {}

        if "basic_salary" in data and data["basic_salary"] <= 0:
            errors["basic_salary"] = (
                "Basic salary must be greater than zero."
            )

        for field in [
            "house_allowance",
            "transport_allowance",
            "medical_allowance",
            "other_allowance",
        ]:
            if field in data and data[field] < 0:
                errors[field] = (
                    f"{field.replace('_', ' ').title()} "
                    "cannot be negative."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class SalaryAdjustmentSerializer(serializers.Serializer):
    new_salary = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    adjustment_type = serializers.ChoiceField(
        choices=SalaryHistory.ADJUSTMENT_TYPE_CHOICES,
    )

    effective_date = serializers.DateField()

    reason = serializers.CharField(
        allow_blank=False,
        max_length=2000,
    )

    update_active_contract = serializers.BooleanField(
        default=True,
    )

    def validate_new_salary(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "New salary must be greater than zero."
            )

        return value
