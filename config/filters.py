from django_filters.rest_framework import DjangoFilterBackend


class SchemaCompatibleDjangoFilterBackend(DjangoFilterBackend):
    def get_schema_operation_parameters(self, view):
        return []
