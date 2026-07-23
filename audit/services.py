from audit.models import AuditLog


def create_audit_log(
    *,
    user=None,
    action,
    module,
    instance=None,
    description="",
    old_values=None,
    new_values=None,
    metadata=None,
    request=None,
):
    ip_address = None
    user_agent = ""
    request_method = ""
    request_path = ""

    if request:
        ip_address = request.META.get("REMOTE_ADDR")

        user_agent = request.META.get(
            "HTTP_USER_AGENT",
            "",
        )

        request_method = request.method

        request_path = request.path

    AuditLog.objects.create(
        user=user,
        action=action,
        module=module,
        model_name=(
            instance.__class__.__name__
            if instance
            else ""
        ),
        object_id=(
            str(instance.pk)
            if instance
            else ""
        ),
        object_repr=(
            str(instance)
            if instance
            else ""
        ),
        description=description,
        old_values=old_values or {},
        new_values=new_values or {},
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
    )


def log_activity(
    *,
    user=None,
    action,
    module,
    description="",
    object_id=None,
    ip_address=None,
    metadata=None,
    instance=None,
    old_values=None,
    new_values=None,
    request=None,
):
    if request:
        return create_audit_log(
            user=user,
            action=action,
            module=module,
            instance=instance,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            request=request,
        )

    return AuditLog.objects.create(
        user=user,
        action=action,
        module=module,
        model_name=(
            instance.__class__.__name__
            if instance
            else ""
        ),
        object_id=(
            str(object_id)
            if object_id is not None
            else (
                str(instance.pk)
                if instance
                else ""
            )
        ),
        object_repr=(
            str(instance)
            if instance
            else ""
        ),
        description=description,
        old_values=old_values or {},
        new_values=new_values or {},
        metadata=metadata or {},
        ip_address=ip_address,
    )
