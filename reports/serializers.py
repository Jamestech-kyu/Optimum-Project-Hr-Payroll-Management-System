from rest_framework import serializers

from .models import (
    ReportExecution,
    ReportTemplate,
    SavedReport,
)


class ReportTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ReportTemplate
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "created_at",
            "updated_at",
        )

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None

        return (
            obj.created_by.get_full_name()
            or obj.created_by.email
            or obj.created_by.username
        )


class ReportExecutionSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(
        source="template.name",
        read_only=True,
    )

    requested_by_name = serializers.SerializerMethodField()

    generated_file_url = serializers.SerializerMethodField()

    class Meta:
        model = ReportExecution
        fields = "__all__"
        read_only_fields = (
            "requested_by",
            "status",
            "generated_file",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
        )

    def get_requested_by_name(self, obj):
        return (
            obj.requested_by.get_full_name()
            or obj.requested_by.email
            or obj.requested_by.username
        )

    def get_generated_file_url(self, obj):
        if not obj.generated_file:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.generated_file.url
            )

        return obj.generated_file.url


class SavedReportSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = SavedReport
        fields = "__all__"
        read_only_fields = (
            "owner",
            "created_at",
            "updated_at",
        )

    def get_owner_name(self, obj):
        return (
            obj.owner.get_full_name()
            or obj.owner.email
            or obj.owner.username
        )


class ReportGenerationSerializer(serializers.Serializer):
    template_id = serializers.IntegerField()

    export_format = serializers.ChoiceField(
        choices=ReportTemplate.EXPORT_FORMATS,
        required=False,
    )

    filters = serializers.JSONField(
        required=False,
        default=dict,
    )

    def validate_template_id(self, value):
        if not ReportTemplate.objects.filter(
            id=value,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "The selected report template does not exist "
                "or is inactive."
            )

        return value


class ReportPreviewSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=ReportTemplate.REPORT_TYPES,
    )

    filters = serializers.JSONField(
        required=False,
        default=dict,
    )
