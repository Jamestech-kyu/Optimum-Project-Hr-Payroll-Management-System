from django.contrib import admin
from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeWorkExperience,
    EmployeeDependant,
    EmployeeCertification,
    EmployeeSkill,
    EmployeeBankAccount,
    EmployeeAsset,
    SalaryHistory,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "first_name",
        "last_name",
        "department",
        "designation",
        "employment_status",
    )

    search_fields = (
        "employee_number",
        "first_name",
        "last_name",
        "personal_email",
    )

    list_filter = (
        "employment_status",
        "branch",
        "department",
    )


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "document_type",
        "document_name",
        "is_verified",
        "uploaded_by",
        "uploaded_at",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "document_name",
    )

    list_filter = (
        "document_type",
        "is_verified",
    )


@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "institution_name",
        "qualification",
        "course",
        "end_date",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "institution_name",
        "qualification",
    )


@admin.register(EmployeeWorkExperience)
class EmployeeWorkExperienceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "company_name",
        "position",
        "start_date",
        "end_date",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "company_name",
        "position",
    )


@admin.register(EmployeeDependant)
class EmployeeDependantAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "full_name",
        "relationship",
        "date_of_birth",
        "is_beneficiary",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "full_name",
        "relationship",
    )
    list_filter = (
        "relationship",
        "is_beneficiary",
    )


@admin.register(EmployeeCertification)
class EmployeeCertificationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "certification_name",
        "issuing_organization",
        "issue_date",
        "expiry_date",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "certification_name",
        "issuing_organization",
    )
    list_filter = (
        "issuing_organization",
    )


@admin.register(EmployeeSkill)
class EmployeeSkillAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "skill_name",
        "skill_level",
        "years_of_experience",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "skill_name",
    )
    list_filter = (
        "skill_level",
    )


@admin.register(EmployeeBankAccount)
class EmployeeBankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "bank_name",
        "branch_name",
        "account_name",
        "account_number",
        "is_primary",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "bank_name",
        "account_name",
        "account_number",
    )
    list_filter = (
        "is_primary",
    )


@admin.register(EmployeeAsset)
class EmployeeAssetAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "asset_name",
        "asset_code",
        "issue_date",
        "is_returned",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "asset_name",
        "asset_code",
    )
    list_filter = (
        "is_returned",
    )


@admin.register(SalaryHistory)
class SalaryHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "previous_salary",
        "new_salary",
        "adjustment_type",
        "effective_date",
        "changed_by",
        "created_at",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "reason",
    )

    list_filter = (
        "adjustment_type",
        "effective_date",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )
