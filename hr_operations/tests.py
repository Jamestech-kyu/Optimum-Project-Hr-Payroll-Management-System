from django.test import TestCase

from rest_framework import serializers

from .models import (
    PerformanceReview,
    PerformanceGoal,
    DisciplinaryCase,
    Announcement,
    Training,
    TrainingEnrollment,
)


# =========================================================
# PERFORMANCE
# =========================================================

class PerformanceGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceGoal
        fields = [
            "id", "review", "title", "description", "target_date",
            "weight_percentage", "status", "progress_notes",
        ]


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    reviewer_name = serializers.CharField(source="reviewer.__str__", read_only=True)
    goals = PerformanceGoalSerializer(many=True, read_only=True)

    class Meta:
        model = PerformanceReview
        fields = [
            "id", "employee", "employee_name", "reviewer", "reviewer_name",
            "review_period_start", "review_period_end", "overall_rating",
            "strengths", "areas_for_improvement", "reviewer_comments",
            "employee_comments", "status", "created_at", "updated_at", "goals",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("review_period_start", getattr(self.instance, "review_period_start", None))
        end = attrs.get("review_period_end", getattr(self.instance, "review_period_end", None))
        if start and end and end < start:
            raise serializers.ValidationError("Review period end date must be after the start date.")
        return attrs


# =========================================================
# DISCIPLINARY
# =========================================================

class DisciplinaryCaseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    reported_by_name = serializers.CharField(source="reported_by.__str__", read_only=True)

    class Meta:
        model = DisciplinaryCase
        fields = [
            "id", "employee", "employee_name", "reported_by", "reported_by_name",
            "incident_date", "description", "severity", "status", "action_taken",
            "resolution_notes", "hearing_date", "resolved_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["reported_by", "created_at", "updated_at"]


# =========================================================
# ANNOUNCEMENTS
# =========================================================

class AnnouncementSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.CharField(source="posted_by.__str__", read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Announcement
        fields = [
            "id", "title", "body", "audience", "target_department",
            "target_branch", "target_role", "posted_by", "posted_by_name",
            "is_pinned", "publish_at", "expires_at", "created_at", "is_active",
        ]
        read_only_fields = ["posted_by", "created_at"]


# =========================================================
# TRAINING
# =========================================================

class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = [
            "id", "training", "employee", "employee_name",
            "status", "certificate", "enrolled_at",
        ]
        read_only_fields = ["enrolled_at"]


class TrainingSerializer(serializers.ModelSerializer):
    enrollments = TrainingEnrollmentSerializer(many=True, read_only=True)
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Training
        fields = [
            "id", "title", "description", "trainer_name", "start_date", "end_date",
            "location", "is_mandatory", "status", "created_by", "created_at",
            "enrollments", "enrolled_count",
        ]
        read_only_fields = ["created_by", "created_at"]

    def get_enrolled_count(self, obj):
        return obj.enrollments.count()

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError("End date cannot be before the start date.")
        return attrs
