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