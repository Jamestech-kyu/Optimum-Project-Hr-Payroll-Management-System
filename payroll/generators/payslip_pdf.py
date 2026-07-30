import logging
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from payroll.models import Payslip

logger = logging.getLogger(__name__)


def generate_payslip_pdf(payslip):
    """
    Generate a PDF file for one payslip and save it on Payslip.pdf_file.
    """

    if not isinstance(payslip, Payslip):
        raise TypeError(
            "payslip must be an instance of Payslip."
        )

    from weasyprint import CSS, HTML

    payslip = (
        Payslip.objects
        .select_related(
            "employee",
            "payroll_run",
        )
        .prefetch_related(
            "allowances",
            "deductions",
        )
        .get(pk=payslip.pk)
    )

    employee = payslip.employee
    payroll_run = payslip.payroll_run

    allowances = payslip.allowances.all()
    deductions = payslip.deductions.all()

    context = {
        "payslip": payslip,
        "employee": employee,
        "payroll_run": payroll_run,
        "allowances": allowances,
        "deductions": deductions,
        "generated_date": timezone.now(),
        "company_name": getattr(
            settings,
            "COMPANY_NAME",
            "HR Payroll Management System",
        ),
        "company_address": getattr(
            settings,
            "COMPANY_ADDRESS",
            "",
        ),
        "company_email": getattr(
            settings,
            "COMPANY_EMAIL",
            "",
        ),
        "company_phone": getattr(
            settings,
            "COMPANY_PHONE",
            "",
        ),
    }

    html_string = render_to_string(
        "payroll/payslip.html",
        context,
    )

    css_path = (
        Path(settings.BASE_DIR)
        / "payroll"
        / "static"
        / "payroll"
        / "css"
        / "payslip.css"
    )

    pdf_buffer = BytesIO()
    stylesheets = []

    if css_path.exists():
        stylesheets.append(
            CSS(filename=str(css_path))
        )
    else:
        logger.warning(
            "Payslip CSS file was not found at %s",
            css_path,
        )

    HTML(
        string=html_string,
        base_url=str(settings.BASE_DIR),
    ).write_pdf(
        target=pdf_buffer,
        stylesheets=stylesheets,
    )

    pdf_buffer.seek(0)

    safe_employee_name = (
        employee.full_name
        .replace(" ", "_")
        .replace("/", "_")
    )

    filename = (
        f"payslip_{safe_employee_name}_"
        f"{payroll_run.year}_"
        f"{payroll_run.month:02d}.pdf"
    )

    if payslip.pdf_file:
        payslip.pdf_file.delete(
            save=False
        )

    payslip.pdf_file.save(
        filename,
        ContentFile(pdf_buffer.read()),
        save=False,
    )

    payslip.pdf_generated_at = timezone.now()

    payslip.save(
        update_fields=[
            "pdf_file",
            "pdf_generated_at",
        ]
    )

    logger.info(
        "Generated PDF for payslip %s.",
        payslip.id,
    )

    return payslip.pdf_file
