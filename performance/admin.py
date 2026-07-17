from django.contrib import admin

from .models import (
    GoalProgress,
    PerformanceAttachment,
    PerformanceCalibration,
    PerformanceComment,
    PerformanceCycle,
    PerformanceGoal,
    PerformanceReview,
)


@admin.register(PerformanceCycle)
class PerformanceCycleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "start_date",
        "end_date",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "title",
    )


@admin.register(PerformanceGoal)
class PerformanceGoalAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "title",
        "weight",
        "status",
    )

    list_filter = (
        "status",
        "cycle",
    )

    search_fields = (
        "title",
    )


@admin.register(GoalProgress)
class GoalProgressAdmin(admin.ModelAdmin):
    list_display = (
        "goal",
        "progress_percentage",
        "submitted_by",
        "submitted_at",
    )


admin.site.register(PerformanceReview)
admin.site.register(PerformanceComment)
admin.site.register(PerformanceAttachment)
admin.site.register(PerformanceCalibration)
