from datetime import datetime
from django.core.files.base import ContentFile

from .excel import generate_excel_file
from .exports import generate_csv_file
from .pdf import generate_pdf_file
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from attendance.models import AttendanceRecord
from benefits.models import EmployeeBenefit
from contracts.models import EmploymentContract
from employees.models import Employee
from leave_management.models import LeaveRequest
from payroll.models import Payslip
from performance.models import PerformanceReview
from training.models import TrainingEnrollment

from .models import (
    ReportExecution,
    ReportTemplate,
)


def parse_date(value, field_name):
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (TypeError, ValueError):
        raise ValidationError(
            {
                field_name: (
                    "Date must use YYYY-MM-DD format."
                )
            }
        )


def apply_employee_filters(queryset, filters):
    department_id = filters.get("department_id")
    branch_id = filters.get("branch_id")
    employee_id = filters.get("employee_id")
    status = filters.get("status")

    if department_id:
        queryset = queryset.filter(
            department_id=department_id
        )

    if branch_id:
        queryset = queryset.filter(
            branch_id=branch_id
        )

    if employee_id:
        queryset = queryset.filter(
            id=employee_id
        )

    if status:
        queryset = queryset.filter(
            status=status
        )

    return queryset


def generate_employee_report(filters):
    queryset = Employee.objects.select_related(
        "department",
        "branch",
        "designation",
    )

    queryset = apply_employee_filters(
        queryset,
        filters,
    )

    return [
        {
            "employee_id": employee.id,
            "employee_number": employee.employee_number,
            "name": str(employee),
            "department": (
                str(employee.department)
                if employee.department
                else None
            ),
            "branch": (
                str(employee.branch)
                if employee.branch
                else None
            ),
            "designation": (
                str(employee.designation)
                if employee.designation
                else None
            ),
            "status": getattr(
                employee,
                "status",
                None,
            ),
        }
        for employee in queryset
    ]


def generate_attendance_report(filters):
    queryset = AttendanceRecord.objects.select_related(
        "employee",
    )

    employee_id = filters.get("employee_id")
    start_date = parse_date(
        filters.get("start_date"),
        "start_date",
    )
    end_date = parse_date(
        filters.get("end_date"),
        "end_date",
    )

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    if start_date:
        queryset = queryset.filter(
            date__gte=start_date
        )

    if end_date:
        queryset = queryset.filter(
            date__lte=end_date
        )

    return [
        {
            "employee_number": (
                record.employee.employee_number
            ),
            "employee": str(record.employee),
            "date": record.date,
            "check_in": getattr(
                record,
                "check_in_time",
                None,
            ),
            "check_out": getattr(
                record,
                "check_out_time",
                None,
            ),
            "status": getattr(
                record,
                "status",
                None,
            ),
        }
        for record in queryset
    ]


def generate_leave_report(filters):
    queryset = LeaveRequest.objects.select_related(
        "employee",
    )

    employee_id = filters.get("employee_id")
    status = filters.get("status")

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    if status:
        queryset = queryset.filter(
            status=status
        )

    return [
        {
            "employee_number": (
                request.employee.employee_number
            ),
            "employee": str(request.employee),
            "start_date": request.start_date,
            "end_date": request.end_date,
            "status": request.status,
        }
        for request in queryset
    ]


def generate_payroll_report(filters):
    queryset = Payslip.objects.select_related(
        "employee",
    )

    employee_id = filters.get("employee_id")

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    return [
        {
            "employee_number": (
                payslip.employee.employee_number
            ),
            "employee": str(payslip.employee),
            "gross_pay": getattr(
                payslip,
                "gross_pay",
                0,
            ),
            "total_deductions": getattr(
                payslip,
                "total_deductions",
                0,
            ),
            "net_pay": getattr(
                payslip,
                "net_pay",
                0,
            ),
        }
        for payslip in queryset
    ]


def generate_performance_report(filters):
    queryset = PerformanceReview.objects.select_related(
        "employee",
    )

    employee_id = filters.get("employee_id")

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    return [
        {
            "employee_number": (
                review.employee.employee_number
            ),
            "employee": str(review.employee),
            "overall_score": getattr(
                review,
                "overall_score",
                None,
            ),
            "rating": getattr(
                review,
                "overall_rating",
                None,
            ),
            "status": review.status,
        }
        for review in queryset
    ]


def generate_training_report(filters):
    queryset = TrainingEnrollment.objects.select_related(
        "employee",
        "session__course",
    )

    employee_id = filters.get("employee_id")
    status = filters.get("status")

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    if status:
        queryset = queryset.filter(
            status=status
        )

    return [
        {
            "employee_number": (
                enrollment.employee.employee_number
            ),
            "employee": str(enrollment.employee),
            "course": enrollment.session.course.title,
            "status": enrollment.status,
            "enrolled_at": enrollment.enrolled_at,
        }
        for enrollment in queryset
    ]


def generate_contract_report(filters):
    queryset = EmploymentContract.objects.select_related(
        "employee",
    )

    employee_id = filters.get("employee_id")
    status = filters.get("status")

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    if status:
        queryset = queryset.filter(
            status=status
        )

    return [
        {
            "employee_number": (
                contract.employee.employee_number
            ),
            "employee": str(contract.employee),
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "status": contract.status,
        }
        for contract in queryset
    ]


def generate_benefit_report(filters):
    queryset = EmployeeBenefit.objects.select_related(
        "employee",
        "benefit_plan",
    )

    employee_id = filters.get("employee_id")
    status = filters.get("status")

    if employee_id:
        queryset = queryset.filter(
            employee_id=employee_id
        )

    if status:
        queryset = queryset.filter(
            status=status
        )

    return [
        {
            "employee_number": (
                benefit.employee.employee_number
            ),
            "employee": str(benefit.employee),
            "benefit_plan": str(
                benefit.benefit_plan
            ),
            "status": benefit.status,
        }
        for benefit in queryset
    ]


REPORT_GENERATORS = {
    "EMPLOYEE": generate_employee_report,
    "ATTENDANCE": generate_attendance_report,
    "LEAVE": generate_leave_report,
    "PAYROLL": generate_payroll_report,
    "PERFORMANCE": generate_performance_report,
    "TRAINING": generate_training_report,
    "CONTRACT": generate_contract_report,
    "BENEFIT": generate_benefit_report,
}


def generate_report_data(
    report_type,
    filters=None,
):
    generator = REPORT_GENERATORS.get(
        report_type
    )

    if not generator:
        raise ValidationError(
            {
                "report_type": (
                    "This report type is not yet supported."
                )
            }
        )

    return generator(filters or {})
def build_report_file(
    *,
    data,
    export_format,
    title,
):
    export_format = export_format.upper()

    safe_title = (
        title.lower()
        .replace(" ", "_")
        .replace("/", "_")
    )

    if export_format == "CSV":
        content = generate_csv_file(data)
        filename = f"{safe_title}.csv"

    elif export_format == "EXCEL":
        content = generate_excel_file(
            data,
            title=title,
        )
        filename = f"{safe_title}.xlsx"

    elif export_format == "PDF":
        content = generate_pdf_file(
            data,
            title=title,
        )
        filename = f"{safe_title}.pdf"

    else:
        raise ValidationError(
            {
                "export_format": (
                    "Only CSV, EXCEL, and PDF exports "
                    "generate downloadable files."
                )
            }
        )

    return filename, ContentFile(content)


@transaction.atomic
def create_report_execution(
    *,
    template_id,
    requested_by,
    export_format=None,
    filters=None,
):
    template = ReportTemplate.objects.filter(
        id=template_id,
        is_active=True,
    ).first()

    if not template:
        raise ValidationError(
            {
                "template_id": (
                    "The selected report template "
                    "does not exist or is inactive."
                )
            }
        )

    execution = ReportExecution.objects.create(
        template=template,
        requested_by=requested_by,
        export_format=(
            export_format
            or template.default_export_format
        ),
        filters=filters or {},
        status="RUNNING",
        started_at=timezone.now(),
    )

    try:
        data = generate_report_data(
            template.report_type,
            execution.filters,
        )

        if execution.export_format != "JSON":
            filename, generated_file = build_report_file(
                data=data,
                export_format=execution.export_format,
                title=template.name,
            )

            execution.generated_file.save(
                filename,
                generated_file,
                save=False,
            )

        execution.status = "COMPLETED"
        execution.completed_at = timezone.now()

        execution.save(
            update_fields=[
                "generated_file",
                "status",
                "completed_at",
            ]
        )

        return execution, data

    except Exception as exc:
        execution.status = "FAILED"
        execution.error_message = str(exc)
        execution.completed_at = timezone.now()
        execution.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
            ]
        )

        raise
