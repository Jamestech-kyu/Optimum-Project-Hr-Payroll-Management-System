from django.contrib import admin
from .models import (
    LeaveType,
    LeaveBalance,
    LeaveRequest,
    LeaveApproval,
    LeaveAttachment,
    PublicHoliday,
)


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "max_days_per_year", "is_paid", "requires_attachment", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_paid", "requires_attachment", "is_active")


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "year", "allocated_days", "used_days", "remaining_days")
    search_fields = ("employee__employee_number", "employee__first_name", "employee__last_name")
    list_filter = ("year", "leave_type")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "total_days", "status", "created_at")
    search_fields = ("employee__employee_number", "employee__first_name", "employee__last_name")
    list_filter = ("status", "leave_type", "start_date")


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(admin.ModelAdmin):
    list_display = ("leave_request", "approver", "approval_level", "action", "created_at")
    search_fields = ("leave_request__employee__employee_number", "approver__username")
    list_filter = ("approval_level", "action")


@admin.register(LeaveAttachment)
class LeaveAttachmentAdmin(admin.ModelAdmin):
    list_display = ("leave_request", "file", "uploaded_at")


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "is_recurring", "is_paid")
    search_fields = ("name",)
    list_filter = ("is_recurring", "is_paid")