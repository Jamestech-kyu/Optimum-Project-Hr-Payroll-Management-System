from django.contrib import admin
from .models import Branch, Department, Designation


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "location",
        "is_active",
    )
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "branch",
        "code",
        "is_active",
    )
    search_fields = ("name", "code")
    list_filter = ("branch", "is_active")


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "department",
        "is_active",
    )
    search_fields = ("title",)
    list_filter = ("department",)