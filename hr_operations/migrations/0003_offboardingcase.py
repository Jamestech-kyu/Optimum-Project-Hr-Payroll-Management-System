from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("hr_operations", "0002_performancecycle")]

    operations = [migrations.CreateModel(name="OffboardingCase", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("exit_type", models.CharField(choices=[("RESIGNATION", "Resignation"), ("TERMINATION", "Termination"), ("END_OF_CONTRACT", "End of contract"), ("RETIREMENT", "Retirement")], max_length=30)),
        ("reason", models.TextField()), ("last_working_day", models.DateField()),
        ("notice_period_status", models.CharField(default="FULL", max_length=20)),
        ("status", models.CharField(choices=[("PENDING", "Pending"), ("IN_PROGRESS", "In progress"), ("COMPLETED", "Completed"), ("OVERDUE", "Overdue"), ("CANCELLED", "Cancelled")], default="PENDING", max_length=20)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("completed_at", models.DateTimeField(blank=True, null=True)),
        ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offboarding_cases", to="employees.employee")),
        ("initiated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="offboarding_cases_initiated", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ["-created_at"]})]
