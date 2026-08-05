from rest_framework import serializers
from .models import (
    LeaveType,
    LeaveBalance,
    LeaveRequest,
    LeaveApproval,
    LeaveAttachment,
    PublicHoliday,
)


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = "__all__"


def _employee_display_name(employee):
    if not employee:
        return ""
    parts = [employee.first_name, employee.middle_name, employee.last_name]
    return " ".join(part for part in parts if part) or employee.employee_number


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Leave request with the related names the web client displays.

    Without these the client only receives foreign-key ids and renders blank
    rows, so the approval screens cannot show who requested what.
    """

    employee_name = serializers.SerializerMethodField()
    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
        default="",
    )
    department_name = serializers.CharField(
        source="employee.department.name",
        read_only=True,
        default="",
    )
    branch_name = serializers.CharField(
        source="employee.branch.name",
        read_only=True,
        default="",
    )
    leave_type_name = serializers.CharField(
        source="leave_type.name",
        read_only=True,
        default="",
    )
    manager_approved_by_name = serializers.CharField(
        source="manager_approved_by.username",
        read_only=True,
        default="",
    )
    hr_approved_by_name = serializers.CharField(
        source="hr_approved_by.username",
        read_only=True,
        default="",
    )

    class Meta:
        model = LeaveRequest
        fields = "__all__"

    def get_employee_name(self, obj):
        return _employee_display_name(obj.employee)


class LeaveApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(
        source="approver.username",
        read_only=True,
        default="",
    )
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveApproval
        fields = "__all__"

    def get_employee_name(self, obj):
        return _employee_display_name(obj.leave_request.employee)


class LeaveAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAttachment
        fields = "__all__"


class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = "__all__"

class CreateLeaveRequestSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    leave_type_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True)


class LeaveApprovalActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class LeaveRejectSerializer(serializers.Serializer):
    reason = serializers.CharField()        

        