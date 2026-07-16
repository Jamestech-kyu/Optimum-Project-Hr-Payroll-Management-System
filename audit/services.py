from .models import AuditLog


def log_activity(
    user,
    action,
    module,
    description,
    object_id="",
    ip_address=None,
):
    """
    Creates a centralized audit log entry.
    """

    AuditLog.objects.create(
        user=user,
        action=action,
        module=module,
        description=description,
        object_id=str(object_id),
        ip_address=ip_address,
    )