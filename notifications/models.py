from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    TYPE_CHOICES = [
        ("GENERAL", "General"),
        ("ANNOUNCEMENT", "Announcement"),
        ("EMPLOYEE", "Employee"),
        ("LEAVE", "Leave"),
        ("ATTENDANCE", "Attendance"),
        ("PAYROLL", "Payroll"),
        ("PAYSLIP", "Payslip"),
        ("CONTRACT", "Contract"),
        ("PERFORMANCE", "Performance"),
        ("TRAINING", "Training"),
        ("BENEFIT", "Benefit"),
        ("SYSTEM", "System"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("NORMAL", "Normal"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    CHANNEL_CHOICES = [
        ("IN_APP", "In-App"),
        ("EMAIL", "Email"),
        ("IN_APP_EMAIL", "In-App and Email"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default="GENERAL",
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="NORMAL",
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default="IN_APP",
    )

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_email_sent = models.BooleanField(
        default=False,
    )

    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    action_url = models.CharField(
        max_length=500,
        blank=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    related_object = GenericForeignKey(
        "content_type",
        "object_id",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["recipient", "is_read"],
                name="notif_recipient_read_idx",
            ),
            models.Index(
                fields=["recipient", "created_at"],
                name="notif_recipient_date_idx",
            ),
            models.Index(
                fields=["notification_type"],
                name="notif_type_idx",
            ),
            models.Index(
                fields=["priority"],
                name="notif_priority_idx",
            ),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()

            self.save(
                update_fields=[
                    "is_read",
                    "read_at",
                    "updated_at",
                ]
            )

        return self

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None

            self.save(
                update_fields=[
                    "is_read",
                    "read_at",
                    "updated_at",
                ]
            )

        return self


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    in_app_enabled = models.BooleanField(
        default=True,
    )

    email_enabled = models.BooleanField(
        default=True,
    )

    leave_notifications = models.BooleanField(
        default=True,
    )

    attendance_notifications = models.BooleanField(
        default=True,
    )

    payroll_notifications = models.BooleanField(
        default=True,
    )

    contract_notifications = models.BooleanField(
        default=True,
    )

    performance_notifications = models.BooleanField(
        default=True,
    )

    training_notifications = models.BooleanField(
        default=True,
    )

    benefit_notifications = models.BooleanField(
        default=True,
    )

    system_notifications = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Notification preference"
        verbose_name_plural = "Notification preferences"

    def __str__(self):
        return f"Notification preferences for {self.user}"


class NotificationBroadcast(models.Model):
    AUDIENCE_CHOICES = [
        ("ALL", "All Users"),
        ("ROLE", "Specific Role"),
        ("DEPARTMENT", "Specific Department"),
        ("BRANCH", "Specific Branch"),
        ("SELECTED_USERS", "Selected Users"),
    ]

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SCHEDULED", "Scheduled"),
        ("SENT", "Sent"),
        ("CANCELLED", "Cancelled"),
    ]

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=Notification.TYPE_CHOICES,
        default="ANNOUNCEMENT",
    )

    priority = models.CharField(
        max_length=20,
        choices=Notification.PRIORITY_CHOICES,
        default="NORMAL",
    )

    channel = models.CharField(
        max_length=20,
        choices=Notification.CHANNEL_CHOICES,
        default="IN_APP",
    )

    audience = models.CharField(
        max_length=30,
        choices=AUDIENCE_CHOICES,
        default="ALL",
    )

    target_role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_broadcasts",
    )

    target_department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_broadcasts",
    )

    selected_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="selected_notification_broadcasts",
    )

    action_url = models.CharField(
        max_length=500,
        blank=True,
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_notification_broadcasts",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
