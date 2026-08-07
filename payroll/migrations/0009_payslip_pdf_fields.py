import uuid

import django.core.validators
from django.db import migrations, models


def populate_verification_codes(apps, schema_editor):
    Payslip = apps.get_model("payroll", "Payslip")

    for payslip in Payslip.objects.filter(
        verification_code__isnull=True
    ):
        payslip.verification_code = uuid.uuid4()
        payslip.save(
            update_fields=[
                "verification_code",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("payroll", "0008_payrollrun_celery_task_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="payslip",
            name="verification_code",
            field=models.UUIDField(
                editable=False,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="payslip",
            name="pdf_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="payslips/%Y/%m/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=[
                            "pdf",
                        ]
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="payslip",
            name="pdf_generated_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_verification_codes,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="payslip",
            name="verification_code",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
