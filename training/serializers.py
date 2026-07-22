from rest_framework import serializers

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


class TrainingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingCategory
        fields = "__all__"


class TrainingCourseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = TrainingCourse
        fields = "__all__"

    def validate_passing_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Passing score must be between 0 and 100."
            )

        return value


class TrainingSessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )

    trainer_name = serializers.CharField(
        source="trainer.get_full_name",
        read_only=True,
    )

    enrolled_participants = serializers.SerializerMethodField()

    class Meta:
        model = TrainingSession
        fields = "__all__"

    def get_enrolled_participants(self, obj):
        return obj.enrollments.filter(
            status__in=["PENDING", "APPROVED", "COMPLETED"]
        ).count()

    def validate(self, data):
        start_date = data.get(
            "start_date",
            getattr(self.instance, "start_date", None),
        )

        end_date = data.get(
            "end_date",
            getattr(self.instance, "end_date", None),
        )

        maximum_participants = data.get(
            "maximum_participants",
            getattr(self.instance, "maximum_participants", None),
        )

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "The session end date must be later "
                        "than its start date."
                    )
                }
            )

        if maximum_participants is not None and maximum_participants < 1:
            raise serializers.ValidationError(
                {
                    "maximum_participants": (
                        "Maximum participants must be at least 1."
                    )
                }
            )

        return data


class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    course_title = serializers.CharField(
        source="session.course.title",
        read_only=True,
    )

    session_start_date = serializers.DateTimeField(
        source="session.start_date",
        read_only=True,
    )

    enrolled_by_name = serializers.CharField(
        source="enrolled_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = TrainingEnrollment
        fields = "__all__"
        read_only_fields = [
            "status",
            "enrolled_by",
            "enrolled_at",
        ]

    def get_employee_name(self, obj):
        if hasattr(obj.employee, "full_name"):
            full_name = obj.employee.full_name
            return full_name() if callable(full_name) else full_name

        return str(obj.employee)


class TrainingAttendanceSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField(
        source="enrollment.employee.employee_number",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    course_title = serializers.CharField(
        source="enrollment.session.course.title",
        read_only=True,
    )

    class Meta:
        model = TrainingAttendance
        fields = "__all__"

    def get_employee_name(self, obj):
        employee = obj.enrollment.employee

        if hasattr(employee, "full_name"):
            full_name = employee.full_name
            return full_name() if callable(full_name) else full_name

        return str(employee)


class TrainingAssessmentSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField(
        source="enrollment.employee.employee_number",
        read_only=True,
    )

    course_title = serializers.CharField(
        source="enrollment.session.course.title",
        read_only=True,
    )

    class Meta:
        model = TrainingAssessment
        fields = "__all__"
        read_only_fields = [
            "passed",
            "assessed_at",
        ]

    def validate_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Assessment score must be between 0 and 100."
            )

        return value


class TrainingCertificateSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField(
        source="enrollment.employee.employee_number",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    course_title = serializers.CharField(
        source="enrollment.session.course.title",
        read_only=True,
    )

    class Meta:
        model = TrainingCertificate
        fields = "__all__"
        read_only_fields = [
            "certificate_number",
            "issued_date",
        ]

    def get_employee_name(self, obj):
        employee = obj.enrollment.employee

        if hasattr(employee, "full_name"):
            full_name = employee.full_name
            return full_name() if callable(full_name) else full_name

        return str(employee)


class TrainingRecommendationSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    course_title = serializers.CharField(
        source="recommended_course.title",
        read_only=True,
    )

    performance_score = serializers.DecimalField(
        source="performance_review.overall_score",
        max_digits=5,
        decimal_places=2,
        read_only=True,
    )

    recommended_by_name = serializers.CharField(
        source="recommended_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = TrainingRecommendation
        fields = "__all__"
        read_only_fields = [
            "recommended_by",
            "created_at",
        ]

    def get_employee_name(self, obj):
        if hasattr(obj.employee, "full_name"):
            full_name = obj.employee.full_name
            return full_name() if callable(full_name) else full_name

        return str(obj.employee)


class TrainingEnrollmentCreateSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    session_id = serializers.IntegerField()


class TrainingEnrollmentActionSerializer(serializers.Serializer):
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class TrainingAttendanceCreateSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()

    attendance_status = serializers.ChoiceField(
        choices=TrainingAttendance.STATUS_CHOICES,
    )

    check_in = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    check_out = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    def validate(self, data):
        check_in = data.get("check_in")
        check_out = data.get("check_out")

        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError(
                {
                    "check_out": (
                        "Check-out time cannot be earlier "
                        "than check-in time."
                    )
                }
            )

        return data


class TrainingAssessmentCreateSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()

    score = serializers.DecimalField(
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


class TrainingRecommendationCreateSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    performance_review_id = serializers.IntegerField()
    recommended_course_id = serializers.IntegerField()
    reason = serializers.CharField()