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
)


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = "__all__"

    def validate(self, data):
        hire_date = data.get("hire_date")
        confirmation_date = data.get("confirmation_date")
        probation_end_date = data.get("probation_end_date")
        basic_salary = data.get("basic_salary")

        branch = data.get("branch")
        department = data.get("department")
        designation = data.get("designation")

        if not branch:
            raise serializers.ValidationError({
                "branch": "Branch is required."
            })

        if not department:
            raise serializers.ValidationError({
                "department": "Department is required."
            })

        if not designation:
            raise serializers.ValidationError({
                "designation": "Designation is required."
            })

        if basic_salary is not None and basic_salary <= 0:
            raise serializers.ValidationError({
                "basic_salary": "Basic salary must be greater than zero."
            })

        if hire_date and confirmation_date and confirmation_date < hire_date:
            raise serializers.ValidationError({
                "confirmation_date": "Confirmation date cannot be before hire date."
            })

        if hire_date and probation_end_date and probation_end_date < hire_date:
            raise serializers.ValidationError({
                "probation_end_date": "Probation end date cannot be before hire date."
            })

        return data

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = "__all__"


class EmployeeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEducation
        fields = "__all__"

class EmployeeWorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeWorkExperience
        fields = "__all__"


class EmployeeDependantSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDependant
        fields = "__all__"


class EmployeeCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCertification
        fields = "__all__"


class EmployeeSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkill
        fields = "__all__"


class EmployeeBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankAccount
        fields = "__all__"


class EmployeeAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAsset
        fields = "__all__"