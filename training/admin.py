from django.contrib import admin

from .models import (
    TrainingAssessment,
    TrainingAttendance,
    TrainingCategory,
    TrainingCertificate,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRecommendation,
    TrainingSession,
)


@admin.register(TrainingCategory)
class TrainingCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "duration_hours",
        "passing_score",
        "cost",
        "is_active",
    )

    list_filter = (
        "category",
        "certificate_enabled",
        "is_active",
    )

    search_fields = ("title",)


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "trainer",
        "start_date",
        "end_date",
        "status",
        "maximum_participants",
    )

    list_filter = (
        "status",
        "course",
    )


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "session",
        "status",
        "enrolled_at",
    )

    list_filter = (
        "status",
        "session",
    )


@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "attendance_status",
        "check_in",
        "check_out",
    )

    list_filter = ("attendance_status",)


@admin.register(TrainingAssessment)
class TrainingAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "score",
        "passed",
        "assessed_at",
    )

    list_filter = ("passed",)


@admin.register(TrainingCertificate)
class TrainingCertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number",
        "enrollment",
        "issued_date",
        "expiry_date",
    )

    search_fields = ("certificate_number",)


@admin.register(TrainingRecommendation)
class TrainingRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "recommended_course",
        "status",
        "recommended_by",
        "created_at",
    )

    list_filter = (
        "status",
        "recommended_course",
    )