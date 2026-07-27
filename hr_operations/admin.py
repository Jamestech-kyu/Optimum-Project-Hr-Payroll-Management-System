from django.contrib import admin

from .models import (
    PerformanceReview,
    PerformanceGoal,
    DisciplinaryCase,
    Announcement,
    Training,
    TrainingEnrollment,
)


class PerformanceGoalInline(admin.TabularInline):
    model = PerformanceGoal
    extra = 1


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "reviewer", "review_period_start",
        "review_period_end", "overall_rating", "status",
    )
    list_filter = ("status", "overall_rating")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_number")
    inlines = [PerformanceGoalInline]


@admin.register(PerformanceGoal)
class PerformanceGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "review", "status", "target_date", "weight_percentage")
    list_filter = ("status",)
    search_fields = ("title",)


@admin.register(DisciplinaryCase)
class DisciplinaryCaseAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "incident_date", "severity",
        "status", "action_taken", "reported_by",
    )
    list_filter = ("severity", "status", "action_taken")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_number", "description")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title", "audience", "is_pinned",
        "publish_at", "expires_at", "posted_by",
    )
    list_filter = ("audience", "is_pinned")
    search_fields = ("title", "body")


class TrainingEnrollmentInline(admin.TabularInline):
    model = TrainingEnrollment
    extra = 1


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = (
        "title", "trainer_name", "start_date", "end_date",
        "is_mandatory", "status", "created_by",
    )
    list_filter = ("status", "is_mandatory")
    search_fields = ("title", "trainer_name")
    inlines = [TrainingEnrollmentInline]


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("employee", "training", "status", "enrolled_at")
    list_filter = ("status",)
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_number")