from django.forms.models import model_to_dict

from .services import create_audit_log


def serialize_instance(instance):
    """
    Convert a Django model instance into JSON-friendly audit data.
    """
    data = model_to_dict(instance)

    for key, value in data.items():
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        elif not isinstance(
            value,
            (str, int, float, bool, list, dict, type(None)),
        ):
            data[key] = str(value)

    return data


class AuditViewSetMixin:
    """
    Automatically records CREATE, UPDATE and DELETE actions.

    Each ViewSet using this mixin should define:

        audit_module = "EMPLOYEES"
    """

    audit_module = "GENERAL"

    def perform_create(self, serializer):
        instance = serializer.save()

        create_audit_log(
            user=self.request.user,
            action="CREATE",
            module=self.audit_module,
            instance=instance,
            description=f"Created {instance.__class__.__name__}.",
            new_values=serialize_instance(instance),
            request=self.request,
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        old_values = serialize_instance(instance)

        updated_instance = serializer.save()
        new_values = serialize_instance(updated_instance)

        create_audit_log(
            user=self.request.user,
            action="UPDATE",
            module=self.audit_module,
            instance=updated_instance,
            description=f"Updated {updated_instance.__class__.__name__}.",
            old_values=old_values,
            new_values=new_values,
            request=self.request,
        )

    def perform_destroy(self, instance):
        old_values = serialize_instance(instance)

        create_audit_log(
            user=self.request.user,
            action="DELETE",
            module=self.audit_module,
            instance=instance,
            description=f"Deleted {instance.__class__.__name__}.",
            old_values=old_values,
            request=self.request,
        )

        instance.delete()