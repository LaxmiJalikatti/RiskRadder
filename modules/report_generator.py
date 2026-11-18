"""
report_generator.py
Creates a PDF analysis report using ReportLab.
"""

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from modules.recommender import DISCLAIMER, add_guidance

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"

SEVERITY_COLORS = {
    "High": colors.HexColor("#D64545"),
    "Medium": colors.HexColor("#E8A317"),
    "Low": colors.HexColor("#2E9E6B"),
}
DARK = colors.HexColor("#0D1B1A")
GREEN = colors.HexColor("#0E9F78")
LIGHT = colors.HexColor("#F1F6F4")
GREY = colors.HexColor("#5B6B68")
SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
PAGE_WIDTH = 170 * mm  # usable width with 20 mm margins


def _styles():
    base = getSampleStyleSheet()["Normal"]

    def make(name, **kwargs):
        kwargs.setdefault("fontName", "Helvetica")
        return ParagraphStyle(name, parent=base, **kwargs)

    return {
        "title": make("title", fontSize=24, leading=28, textColor=colors.white,
                      fontName="Helvetica-Bold"),
        "subtitle": make("subtitle", fontSize=12, leading=16,
                         textColor=colors.HexColor("#2DD4A7")),
        "meta": make("meta", fontSize=9, leading=13, textColor=GREY),
        "heading": make("heading", fontSize=14, leading=18, textColor=DARK,
                        fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6),
        "body": make("body", fontSize=10, leading=14, textColor=DARK),
        "bold": make("bold", fontSize=10, leading=14, textColor=DARK,
                     fontName="Helvetica-Bold"),
        "label": make("label", fontSize=9, leading=12, textColor=GREY,
                      fontName="Helvetica-Bold"),
        "white": make("white", fontSize=10, leading=13, textColor=colors.white,
                      fontName="Helvetica-Bold"),
        "score": make("score", fontSize=14, leading=40, textColor=colors.white,
                      alignment=1),
        "level": make("level", fontSize=11, leading=14, textColor=colors.white,
                      fontName="Helvetica-Bold", alignment=1),
    }


def _p(text, style):
    return Paragraph(escape(str(text)), style)


def _header_block(styles, source_name, result):
    header = Table(
        [
            [Paragraph("RiskRadder", styles["title"])],
            [Paragraph("Terms and Conditions Risk Analysis Report",
                       styles["subtitle"])],
        ],
        colWidths=[PAGE_WIDTH],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
    ]))
    date_text = datetime.now().strftime("%d %B %Y, %I:%M %p")
    meta = _p(
        f"Document: {source_name}   |   Generated: {date_text}   |   "
        f"Clauses analysed: {result['total_clauses']}",
        styles["meta"],
    )
    return [header, Spacer(1, 6), meta, Spacer(1, 10)]


def _score_block(styles, result):
    color = SEVERITY_COLORS[result["level"]]
    score_cell = [
        Paragraph(
            f'<font size="34"><b>{result["score"]}</b></font>/100',
            styles["score"],
        ),
        Paragraph(f"{result['level'].upper()} RISK", styles["level"]),
    ]
    text_cell = [
        _p(result["summary"], styles["body"]),
        Spacer(1, 6),
        _p(result["overall_advice"], styles["bold"]),
    ]
    table = Table([[score_cell, text_cell]], colWidths=[45 * mm, 125 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("RIGHTPADDING", (1, 0), (1, 0), 12),
    ]))
    return [table, Spacer(1, 8)]


def _count_tables(styles, result):
    severity_rows = [[_p("Severity", styles["white"]),
                      _p("Clauses", styles["white"])]]
    for level in ("High", "Medium", "Low"):
        severity_rows.append(
            [_p(level, styles["bold"]),
             _p(result["severity_counts"][level], styles["body"])]
        )
    severity = Table(severity_rows, colWidths=[35 * mm, 25 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.white),
    ]
    for row, level in enumerate(("High", "Medium", "Low"), start=1):
        style.append(("LINEBEFORE", (0, row), (0, row), 4, SEVERITY_COLORS[level]))
    severity.setStyle(TableStyle(style))

    category_rows = [[_p("Risk category", styles["white"]),
                      _p("Found", styles["white"])]]
    ordered = sorted(result["category_counts"].items(), key=lambda kv: -kv[1])
    for name, count in ordered:
        category_rows.append([_p(name, styles["body"]), _p(count, styles["body"])])
    categories = Table(category_rows, colWidths=[65 * mm, 20 * mm])
    categories.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.white),
    ]))

    side_by_side = Table([[severity, categories]],
                         colWidths=[75 * mm, 95 * mm])
    side_by_side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [side_by_side]


def _clause_card(styles, item):
    color = SEVERITY_COLORS[item["severity"]]
    title = (
        f"{item['severity'].upper()}   |   {item['category']}   |   "
        f"Clause {item['id']}"
    )
    rows = [
        [_p(title, styles["white"]), ""],
        [_p("Clause", styles["label"]), _p(item["original"], styles["body"])],
        [_p("Why it matters", styles["label"]),
         _p(item["explanation"], styles["body"])],
        [_p("What to do", styles["label"]),
         _p(item["recommendation"], styles["body"])],
    ]
    card = Table(rows, colWidths=[32 * mm, 138 * mm])
    card.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), color),
        ("BACKGROUND", (0, 1), (1, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.white),
    ]))
    return KeepTogether([card, Spacer(1, 8)])


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 10 * mm, "RiskRadder  |  " + DISCLAIMER)
    canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def generate_report(result, source_name="Pasted text", output_path=None):
    """
    Build the PDF report and return the path of the file.
    `result` is the dictionary from analyze_text() (guidance is added if missing).
    """
    if "summary" not in result:
        add_guidance(result)

    if output_path is None:
        REPORTS_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = REPORTS_DIR / f"RiskRadder_Report_{stamp}.pdf"
    output_path = Path(output_path)

    styles = _styles()
    story = []
    story += _header_block(styles, source_name, result)
    story += _score_block(styles, result)
    story.append(Paragraph("Overview", styles["heading"]))
    story += _count_tables(styles, result)
    story.append(Paragraph("Flagged clauses", styles["heading"]))

    if result["flagged"]:
        ordered = sorted(
            result["flagged"],
            key=lambda i: (SEVERITY_ORDER[i["severity"]], i["id"]),
        )
        for item in ordered:
            story.append(_clause_card(styles, item))
    else:
        story.append(_p("No risky clauses were detected.", styles["body"]))

    story.append(Spacer(1, 6))
    story.append(_p(result["disclaimer"], styles["meta"]))

    document = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title="RiskRadder Analysis Report", author="RiskRadder",
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output_path
