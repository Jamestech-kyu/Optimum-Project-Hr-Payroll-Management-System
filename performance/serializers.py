from rest_framework import serializers

from .models import (
    GoalProgress,
    PerformanceAttachment,
    PerformanceCalibration,
    PerformanceComment,
    PerformanceCycle,
    PerformanceGoal,
    PerformanceReview,
)


class PerformanceCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceCycle
        fields = "__all__"


class PerformanceGoalSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    cycle_name = serializers.CharField(
        source="cycle.title",
        read_only=True,
    )

    class Meta:
        model = PerformanceGoal
        fields = "__all__"

    def get_employee_name(self, obj):
        if hasattr(obj.employee, "full_name"):
            full_name = obj.employee.full_name
            return full_name() if callable(full_name) else full_name
        return str(obj.employee)


class GoalProgressSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(
        source="submitted_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = GoalProgress
        fields = "__all__"


class GoalProgressCreateSerializer(serializers.Serializer):
    goal_id = serializers.IntegerField()

    progress_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
    )

    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    reviewer_name = serializers.CharField(
        source="reviewer.get_full_name",
        read_only=True,
    )

    cycle_name = serializers.CharField(
        source="cycle.title",
        read_only=True,
    )

    class Meta:
        model = PerformanceReview
        fields = "__all__"
        read_only_fields = [
            "overall_score",
            "overall_rating",
            "created_at",
            "updated_at",
        ]

    def get_employee_name(self, obj):
        if hasattr(obj.employee, "full_name"):
            full_name = obj.employee.full_name
            return full_name() if callable(full_name) else full_name
        return str(obj.employee)


class PerformanceCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source="author.get_full_name",
        read_only=True,
    )

    class Meta:
        model = PerformanceComment
        fields = "__all__"


class PerformanceAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = PerformanceAttachment
        fields = "__all__"


class PerformanceCalibrationSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = PerformanceCalibration
        fields = "__all__"


class ReviewActionSerializer(serializers.Serializer):
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
