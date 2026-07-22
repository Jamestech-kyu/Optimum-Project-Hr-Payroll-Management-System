import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_file(
    data,
    title="HRMS Report",
):
    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph(
            title,
            styles["Title"],
        ),
        Spacer(1, 0.2 * inch),
    ]

    if not data:
        elements.append(
            Paragraph(
                "No data available.",
                styles["Normal"],
            )
        )

        document.build(elements)
        output.seek(0)

        return output.getvalue()

    headers = list(data[0].keys())

    table_data = [
        [
            Paragraph(
                str(header)
                .replace("_", " ")
                .title(),
                styles["BodyText"],
            )
            for header in headers
        ]
    ]

    for row in data:
        table_data.append(
            [
                Paragraph(
                    str(
                        row.get(header, "")
                        if row.get(header) is not None
                        else ""
                    ),
                    styles["BodyText"],
                )
                for header in headers
            ]
        )

    available_width = landscape(A4)[0] - 40

    column_width = available_width / max(
        len(headers),
        1,
    )

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            column_width
            for _ in headers
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(table)

    document.build(elements)

    output.seek(0)

    return output.getvalue()