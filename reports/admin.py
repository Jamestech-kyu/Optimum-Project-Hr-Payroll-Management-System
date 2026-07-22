from django.contrib import admin

from .models import (
    ReportTemplate,
    ReportExecution,
    SavedReport,
)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "report_type",
        "default_export_format",
        "is_active",
        "created_at",
    )

    list_filter = (
        "report_type",
        "default_export_format",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "template",
        "requested_by",
        "export_format",
        "status",
        "created_at",
        "completed_at",
    )

    list_filter = (
        "status",
        "export_format",
    )

    readonly_fields = (
        "created_at",
        "started_at",
        "completed_at",
    )


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "report_type",
        "export_format",
        "is_public",
    )

    list_filter = (
        "report_type",
        "export_format",
        "is_public",
    )

    search_fields = (
        "name",
    )