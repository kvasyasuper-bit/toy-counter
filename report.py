
import os
from datetime import datetime

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from database import get_history

REPORT_DIR = "static/results"


def export_excel() -> str:
    history = get_history(limit=1000)

    wb = Workbook()
    ws = wb.active
    ws.title = "История"
    ws.append(["ID", "Дата и время", "Файл", "Найдено игрушек"])

    for row in history:
        ws.append([row["id"], row["timestamp"], row["filename"], row["count"]])

    widths = [8, 22, 30, 18]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    path = os.path.join(REPORT_DIR, "report.xlsx")
    os.makedirs(REPORT_DIR, exist_ok=True)
    wb.save(path)
    return path


def export_pdf() -> str:
    history = get_history(limit=1000)

    path = os.path.join(REPORT_DIR, "report.pdf")
    os.makedirs(REPORT_DIR, exist_ok=True)

    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Report: Toy detection history", styles["Title"]),
        Paragraph("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  styles["Normal"]),
        Spacer(1, 12),
    ]

    data = [["ID", "Timestamp", "File", "Toys"]]
    for row in history:
        data.append([row["id"], row["timestamp"], row["filename"], row["count"]])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
    ]))
    elements.append(table)

    doc.build(elements)
    return path
