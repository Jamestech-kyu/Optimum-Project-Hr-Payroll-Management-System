from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def money(value):
    return f"{value:,.2f}"


def generate_payslip_pdf(payslip):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Payslip - {payslip.employee.employee_number}",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PayslipTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "PayslipSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=15,
    )

    right_style = ParagraphStyle(
        "RightText",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )

    story = []

    payroll_run = payslip.payroll_run
    employee = payslip.employee

    story.append(
        Paragraph(
            "HR PAYROLL SYSTEM",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"PAYSLIP FOR {payroll_run.month:02d}/{payroll_run.year}",
            subtitle_style,
        )
    )

    employee_data = [
        [
            Paragraph("<b>Employee Number</b>", styles["Normal"]),
            employee.employee_number,
            Paragraph("<b>Employee Name</b>", styles["Normal"]),
            employee.full_name,
        ],
        [
            Paragraph("<b>Department</b>", styles["Normal"]),
            employee.department.name if employee.department else "-",
            Paragraph("<b>Designation</b>", styles["Normal"]),
            employee.designation.name if employee.designation else "-",
        ],
        [
            Paragraph("<b>Branch</b>", styles["Normal"]),
            employee.branch.name if employee.branch else "-",
            Paragraph("<b>Employment Type</b>", styles["Normal"]),
            employee.get_employment_type_display(),
        ],
    ]

    employee_table = Table(
        employee_data,
        colWidths=[
            38 * mm,
            50 * mm,
            38 * mm,
            50 * mm,
        ],
    )

    employee_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(employee_table)
    story.append(Spacer(1, 10 * mm))

    earnings_rows = [
        [
            Paragraph("<b>Earnings</b>", styles["Normal"]),
            Paragraph("<b>Amount</b>", right_style),
        ],
        [
            "Basic Salary",
            Paragraph(money(payslip.basic_salary), right_style),
        ],
    ]

    for allowance in payslip.allowances.all():
        earnings_rows.append([
            allowance.name,
            Paragraph(money(allowance.amount), right_style),
        ])

    earnings_rows.append([
        Paragraph("<b>Gross Pay</b>", styles["Normal"]),
        Paragraph(
            f"<b>{money(payslip.gross_pay)}</b>",
            right_style,
        ),
    ])

    earnings_table = Table(
        earnings_rows,
        colWidths=[125 * mm, 50 * mm],
    )

    earnings_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(earnings_table)
    story.append(Spacer(1, 8 * mm))

    deduction_rows = [
        [
            Paragraph("<b>Deductions</b>", styles["Normal"]),
            Paragraph("<b>Amount</b>", right_style),
        ]
    ]

    for deduction in payslip.deductions.all():
        deduction_rows.append([
            deduction.name,
            Paragraph(money(deduction.amount), right_style),
        ])

    deduction_rows.append([
        Paragraph("<b>Total Deductions</b>", styles["Normal"]),
        Paragraph(
            f"<b>{money(payslip.total_deductions)}</b>",
            right_style,
        ),
    ])

    deduction_table = Table(
        deduction_rows,
        colWidths=[125 * mm, 50 * mm],
    )

    deduction_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4CCCC")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(deduction_table)
    story.append(Spacer(1, 10 * mm))

    net_pay_table = Table(
        [[
            Paragraph("<b>NET PAY</b>", styles["Heading2"]),
            Paragraph(
                f"<b>{money(payslip.net_pay)}</b>",
                right_style,
            ),
        ]],
        colWidths=[125 * mm, 50 * mm],
    )

    net_pay_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D9EAD3")),
            ("BOX", (0, 0), (-1, -1), 1, colors.darkgreen),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    story.append(net_pay_table)
    story.append(Spacer(1, 15 * mm))

    story.append(
        Paragraph(
            "This payslip was generated electronically and does not require a signature.",
            subtitle_style,
        )
    )

    document.build(story)

    buffer.seek(0)
    return buffer