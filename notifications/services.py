from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser

from .models import (
    Notification,
    NotificationBroadcast,
    NotificationPreference,
)


def get_or_create_preferences(user):
    preferences, _ = NotificationPreference.objects.get_or_create(
        user=user
    )

    return preferences


@transaction.atomic
def create_notification(
    *,
    recipient,
    title,
    message,
    notification_type="GENERAL",
    priority="NORMAL",
    channel="IN_APP",
    sender=None,
    related_object=None,
    action_url="",
    metadata=None,
):
    preferences = get_or_create_preferences(recipient)

    if not preferences.in_app_enabled:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        channel=channel,
        action_url=action_url,
        metadata=metadata or {},
    )

    if related_object:
        notification.content_type = ContentType.objects.get_for_model(
            related_object
        )

        notification.object_id = related_object.pk

        notification.save(
            update_fields=[
                "content_type",
                "object_id",
            ]
        )

    if (
        channel in ["EMAIL", "IN_APP_EMAIL"]
        and preferences.email_enabled
    ):
        send_notification_email(notification)

    return notification


@transaction.atomic
def create_bulk_notifications(
    *,
    recipients,
    title,
    message,
    notification_type="GENERAL",
    priority="NORMAL",
    channel="IN_APP",
    sender=None,
    related_object=None,
):
    notifications = []

    for recipient in recipients:
        notification = create_notification(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channel=channel,
            related_object=related_object,
        )

        if notification:
            notifications.append(notification)

    return notifications


def send_notification_email(notification):
    if not notification.recipient.email:
        return

    send_mail(
        subject=notification.title,
        message=notification.message,
        from_email=None,
        recipient_list=[notification.recipient.email],
        fail_silently=True,
    )

    notification.is_email_sent = True
    notification.email_sent_at = timezone.now()

    notification.save(
        update_fields=[
            "is_email_sent",
            "email_sent_at",
        ]
    )


@transaction.atomic
def mark_notification_as_read(notification):
    notification.mark_as_read()

    return notification


@transaction.atomic
def mark_all_notifications_as_read(user):
    unread = Notification.objects.filter(
        recipient=user,
        is_read=False,
    )

    count = unread.count()

    unread.update(
        is_read=True,
        read_at=timezone.now(),
    )

    return count


def unread_notification_count(user):
    return Notification.objects.filter(
        recipient=user,
        is_read=False,
    ).count()


def total_notification_count(user):
    return Notification.objects.filter(
        recipient=user,
    ).count()


def recent_notifications(
    user,
    limit=10,
):
    return Notification.objects.filter(
        recipient=user,
    )[:limit]


@transaction.atomic
def send_broadcast(broadcast):
    if broadcast.status == "SENT":
        return 0

    if broadcast.audience == "ALL":
        recipients = CustomUser.objects.filter(
            is_active=True
        )

    elif broadcast.audience == "ROLE":
        recipients = CustomUser.objects.filter(
            role=broadcast.target_role,
            is_active=True,
        )

    elif broadcast.audience == "DEPARTMENT":
        recipients = CustomUser.objects.filter(
            employee_profile__department=broadcast.target_department,
            is_active=True,
        )

    elif broadcast.audience == "SELECTED_USERS":
        recipients = broadcast.selected_users.filter(
            is_active=True
        )

    else:
        recipients = CustomUser.objects.none()

    create_bulk_notifications(
        recipients=recipients,
        title=broadcast.title,
        message=broadcast.message,
        notification_type=broadcast.notification_type,
        priority=broadcast.priority,
        channel=broadcast.channel,
        sender=broadcast.created_by,
    )

    broadcast.status = "SENT"
    broadcast.sent_at = timezone.now()

    broadcast.save(
        update_fields=[
            "status",
            "sent_at",
        ]
    )

    return recipients.count()
