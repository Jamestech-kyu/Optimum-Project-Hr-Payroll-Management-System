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


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = "__all__"


class LeaveApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApproval
        fields = "__all__"


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

        