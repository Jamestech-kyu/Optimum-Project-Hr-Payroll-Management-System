# Generated manually to align the database with the current payroll engine.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def normalize_payroll_run_statuses(apps, schema_editor):
    PayrollRun = apps.get_model("payroll", "PayrollRun")

    status_map = {
        "draft": "DRAFT",
        "processing": "PENDING_APPROVAL",
        "completed": "APPROVED",
        "disbursed": "FINALIZED",
    }

    for old_status, new_status in status_map.items():
        PayrollRun.objects.filter(status=old_status).update(
            status=new_status
        )


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0008_salaryhistory"),
        ("payroll", "0003_currency_statutoryrate_taxband_payrollpolicy_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(
            name="BankDisbursement",
        ),
        migrations.DeleteModel(
            name="Payslip",
        ),
        migrations.DeleteModel(
            name="PayrollDeduction",
        ),
        migrations.DeleteModel(
            name="Payroll",
        ),
        migrations.DeleteModel(
            name="SalaryStructure",
        ),
        migrations.DeleteModel(
            name="DeductionType",
        ),
        migrations.DeleteModel(
            name="TaxSlab",
        ),
        migrations.RenameField(
            model_name="payrollrun",
            old_name="period_month",
            new_name="month",
        ),
        migrations.RenameField(
            model_name="payrollrun",
            old_name="period_year",
            new_name="year",
        ),
        migrations.RenameField(
            model_name="payrollrun",
            old_name="run_status",
            new_name="status",
        ),
        migrations.RenameField(
            model_name="payrollrun",
            old_name="completed_at",
            new_name="approved_at",
        ),
        migrations.RenameField(
            model_name="payrollrun",
            old_name="initiated_by",
            new_name="processed_by",
        ),
        migrations.AlterField(
            model_name="payrollrun",
            name="month",
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name="payrollrun",
            name="year",
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name="payrollrun",
            name="processed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="payroll_runs_processed",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="payrollrun",
            name="approved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="payroll_runs_approved",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="payrollrun",
            name="processed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="payrollrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("PENDING_APPROVAL", "Pending Approval"),
                    ("APPROVED", "Approved"),
                    ("FINALIZED", "Finalized"),
                    ("CANCELLED", "Cancelled"),
                ],
                default="DRAFT",
                max_length=30,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="payrollrun",
            unique_together={("month", "year")},
        ),
        migrations.AlterModelOptions(
            name="payrollrun",
            options={"ordering": ["-year", "-month"]},
        ),
        migrations.RunPython(
            normalize_payroll_run_statuses,
            migrations.RunPython.noop,
        ),
        migrations.CreateModel(
            name="Payslip",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "basic_salary",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "total_allowances",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "gross_pay",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "total_deductions",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "tax_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "net_pay",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payslips",
                        to="employees.employee",
                    ),
                ),
                (
                    "payroll_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payslips",
                        to="payroll.payrollrun",
                    ),
                ),
            ],
            options={
                "unique_together": {("payroll_run", "employee")},
            },
        ),
        migrations.CreateModel(
            name="PayrollAllowance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                    ),
                ),
                (
                    "payslip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allowances",
                        to="payroll.payslip",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PayrollDeduction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                    ),
                ),
                (
                    "payslip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deductions",
                        to="payroll.payslip",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BankPayment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bank_name", models.CharField(max_length=150)),
                ("account_number", models.CharField(max_length=100)),
                ("account_name", models.CharField(max_length=150)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PROCESSING", "Processing"),
                            ("PAID", "Paid"),
                            ("FAILED", "Failed"),
                        ],
                        default="PENDING",
                        max_length=30,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bank_payments",
                        to="employees.employee",
                    ),
                ),
                (
                    "payroll_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bank_payments",
                        to="payroll.payrollrun",
                    ),
                ),
            ],
        ),
    ]
