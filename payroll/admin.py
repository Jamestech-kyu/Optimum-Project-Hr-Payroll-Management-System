from django.contrib import admin
from .models import (
    PayrollRun,
    Payslip,
    PayrollDeduction,
    PayrollAllowance,
    BankPayment,
    PayComponent,
    EmployeePayComponent,
    TaxBand,
    StatutoryRate,
    Currency,
    ExchangeRate,
    PayrollPolicy,
)


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = (
        "month",
        "year",
        "status",
        "processed_by",
        "approved_by",
        "created_at",
    )

    list_filter = (
        "status",
        "year",
        "month",
    )

    search_fields = (
        "month",
        "year",
    )


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "payroll_run",
        "gross_pay",
        "total_deductions",
        "tax_amount",
        "net_pay",
    )

    list_filter = (
        "payroll_run",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
    )


@admin.register(PayrollDeduction)
class PayrollDeductionAdmin(admin.ModelAdmin):
    list_display = (
        "payslip",
        "name",
        "amount",
    )

    search_fields = (
        "name",
    )


@admin.register(PayrollAllowance)
class PayrollAllowanceAdmin(admin.ModelAdmin):
    list_display = (
        "payslip",
        "name",
        "amount",
    )

    search_fields = (
        "name",
    )


@admin.register(BankPayment)
class BankPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "bank_name",
        "account_number",
        "amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "bank_name",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
    )

@admin.register(PayComponent)
class PayComponentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "component_type",
        "calculation_type",
        "default_amount",
        "percentage_rate",
        "is_taxable",
        "is_active",
    )

    search_fields = ("name", "code")
    list_filter = ("component_type", "calculation_type", "is_taxable", "is_active")


@admin.register(EmployeePayComponent)
class EmployeePayComponentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "component",
        "amount",
        "is_active",
    )

    search_fields = (
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "component__name",
    )

    list_filter = (
        "component__component_type",
        "is_active",
    )    

@admin.register(TaxBand)
class TaxBandAdmin(admin.ModelAdmin):
    list_display = ("name", "min_income", "max_income", "rate", "effective_from", "is_active")
    list_filter = ("name", "is_active", "effective_from")


@admin.register(StatutoryRate)
class StatutoryRateAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "statutory_type", "rate", "is_percentage", "effective_from", "is_active")
    search_fields = ("name", "code")
    list_filter = ("statutory_type", "is_active")


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "is_base_currency", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_base_currency", "is_active")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("from_currency", "to_currency", "rate", "effective_date", "is_active")
    list_filter = ("from_currency", "to_currency", "effective_date")


@admin.register(PayrollPolicy)
class PayrollPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "working_days_per_month",
        "working_hours_per_day",
        "overtime_multiplier",
        "payroll_cutoff_day",
        "payslip_generation_day",
        "currency",
        "is_active",
    )
