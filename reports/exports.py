import csv
import io


def generate_csv_file(data):
    output = io.StringIO()

    if not data:
        writer = csv.writer(output)
        writer.writerow(["No data available"])
        return output.getvalue().encode("utf-8")

    fieldnames = list(data[0].keys())

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    for row in data:
        writer.writerow(
            {
                key: (
                    value.isoformat()
                    if hasattr(value, "isoformat")
                    else value
                )
                for key, value in row.items()
            }
        )

    return output.getvalue().encode("utf-8")