from rest_framework import serializers

from .models import (
    BranchTask,
    EmployeeNote,
    PerformanceCycle,
    PerformanceReview,
    PerformanceGoal,
    DisciplinaryCase,
    Announcement,
    Training,
    TrainingEnrollment,
    OffboardingCase,
    OffboardingChecklistItem,
    OffboardingExitInterview,
    OffboardingFinalSettlement,
)


def employee_display_name(employee):
    """Employee has no ``full_name`` field, so compose one from its parts."""
    if not employee:
        return ""
    parts = [employee.first_name, employee.middle_name, employee.last_name]
    return " ".join(part for part in parts if part) or employee.employee_number


# =========================================================
# PERFORMANCE
# =========================================================

class PerformanceGoalSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceGoal
        fields = [
            "id", "review", "employee", "employee_name", "cycle", "title",
            "description", "target_date", "weight_percentage", "status",
            "progress_notes", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_employee_name(self, obj):
        return employee_display_name(obj.owner)

    def validate(self, attrs):
        # A goal must belong to somebody: either directly or via its review.
        employee = attrs.get("employee") or getattr(self.instance, "employee", None)
        review = attrs.get("review") or getattr(self.instance, "review", None)
        if not employee and not review:
            raise serializers.ValidationError(
                "Provide an employee (or a review) for this goal."
            )
        return attrs


class PerformanceCycleSerializer(serializers.ModelSerializer):
    """Appraisal cycle as the web client's Performance Oversight page models it."""

    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True,
        default="",
    )

    class Meta:
        model = PerformanceCycle
        fields = [
            "id", "name", "description", "start_date", "end_date",
            "review_period", "status", "scope", "scope_id", "rating_scale",
            "has_360_feedback", "reminder_frequency", "employees",
            "employee_status", "created_at", "created_by", "created_by_name",
        ]
        read_only_fields = ["created_at", "created_by"]


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    reviewer_name = serializers.CharField(
        source="reviewer.username",
        read_only=True,
        default="",
    )
    goals = PerformanceGoalSerializer(many=True, read_only=True)

    def get_employee_name(self, obj):
        return employee_display_name(obj.employee)

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


class OffboardingCaseSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    employee_email = serializers.CharField(source="employee.work_email", read_only=True)
    branch_name = serializers.CharField(source="employee.branch.name", read_only=True)
    department_name = serializers.CharField(source="employee.department.name", read_only=True)
    position = serializers.CharField(source="employee.designation.title", read_only=True)
    initiated_by_name = serializers.SerializerMethodField()
    checklist_total = serializers.SerializerMethodField()
    checklist_completed = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        return employee_display_name(obj.employee)

    def get_initiated_by_name(self, obj):
        if not obj.initiated_by:
            return ""
        return obj.initiated_by.get_full_name() or obj.initiated_by.username

    def get_checklist_total(self, obj):
        return obj.checklist_items.count()

    def get_checklist_completed(self, obj):
        return obj.checklist_items.filter(status="COMPLETED").count()

    class Meta:
        model = OffboardingCase
        fields = ["id", "employee", "employee_name", "employee_number", "employee_email", "branch_name", "department_name", "position", "exit_type", "reason", "last_working_day", "notice_period_status", "status", "initiated_by", "initiated_by_name", "checklist_total", "checklist_completed", "created_at", "updated_at", "completed_at"]
        read_only_fields = ["initiated_by", "created_at", "updated_at", "completed_at"]


class OffboardingChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffboardingChecklistItem
        fields = "__all__"


class OffboardingExitInterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffboardingExitInterview
        fields = "__all__"


class OffboardingFinalSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffboardingFinalSettlement
        fields = "__all__"


# =========================================================
# BRANCH OPERATIONS
# =========================================================

class BranchTaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True, default="",
    )

    class Meta:
        model = BranchTask
        fields = [
            "id", "title", "description", "priority", "status", "due_date",
            "assigned_to", "assigned_to_name", "branch", "department",
            "created_by", "created_by_name", "completed_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def get_assigned_to_name(self, obj):
        return employee_display_name(obj.assigned_to)


class EmployeeNoteSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    author_name = serializers.CharField(
        source="author.username", read_only=True, default="",
    )

    class Meta:
        model = EmployeeNote
        fields = [
            "id", "employee", "employee_name", "note", "category",
            "author", "author_name", "created_at",
        ]
        read_only_fields = ["author", "created_at"]

    def get_employee_name(self, obj):
        return employee_display_name(obj.employee)
