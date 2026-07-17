# Generated manually to record employee salary history.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0007_employeeasset"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SalaryHistory",
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
                    "previous_salary",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "new_salary",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                    ),
                ),
                (
                    "adjustment_type",
                    models.CharField(
                        choices=[
                            ("INITIAL", "Initial Salary"),
                            ("INCREMENT", "Salary Increment"),
                            ("DECREMENT", "Salary Decrement"),
                            ("PROMOTION", "Promotion"),
                            ("CONTRACT_RENEWAL", "Contract Renewal"),
                            ("CORRECTION", "Salary Correction"),
                            ("OTHER", "Other"),
                        ],
                        default="OTHER",
                        max_length=30,
                    ),
                ),
                ("effective_date", models.DateField()),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="salary_changes_made",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="salary_history",
                        to="employees.employee",
                    ),
                ),
            ],
            options={
                "ordering": ["-effective_date", "-created_at"],
            },
        ),
    ]
