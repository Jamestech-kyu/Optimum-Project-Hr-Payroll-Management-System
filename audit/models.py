from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
        ("SUBMIT", "Submit"),
        ("DOWNLOAD", "Download"),
        ("EXPORT", "Export"),
        ("VIEW", "View"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )

    module = models.CharField(
        max_length=100,
        db_index=True,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    object_id = models.CharField(
        max_length=100,
        blank=True,
    )

    object_repr = models.CharField(
        max_length=255,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    old_values = models.JSONField(
        default=dict,
        blank=True,
    )

    new_values = models.JSONField(
        default=dict,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    request_method = models.CharField(
        max_length=10,
        blank=True,
    )

    request_path = models.CharField(
        max_length=500,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["module", "action"],
                name="audit_module_action_idx",
            ),
            models.Index(
                fields=["user", "created_at"],
                name="audit_user_date_idx",
            ),
            models.Index(
                fields=["model_name", "object_id"],
                name="audit_object_idx",
            ),
            models.Index(
                fields=["action", "created_at"],
                name="audit_action_date_idx",
            ),
        ]

    def __str__(self):
        username = self.user.email if self.user else "System"

        return (
            f"{username} - {self.action} - "
            f"{self.module} - {self.created_at}"
        )
