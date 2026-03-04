"""
pdf_report_exporter.py — Generare raport PDF complet ISO 19650 pentru un proiect BIM.

Folosește ReportLab pentru a genera un raport profesional cu:
- Pagina de copertă
- Scor overall + scoruri per parte ISO 19650
- Verificări detaliate (pass/warning/fail)
- Recomandări
- Sănătatea proiectului
"""

from __future__ import annotations

import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ── Culori ──────────────────────────────────────────────────────────────

BLUE_DARK = colors.HexColor("#1D4ED8")
BLUE_LIGHT = colors.HexColor("#DBEAFE")
GREEN = colors.HexColor("#16A34A")
GREEN_BG = colors.HexColor("#F0FDF4")
YELLOW = colors.HexColor("#F59E0B")
YELLOW_BG = colors.HexColor("#FFFBEB")
RED = colors.HexColor("#EF4444")
RED_BG = colors.HexColor("#FEF2F2")
GRAY_700 = colors.HexColor("#374151")
GRAY_500 = colors.HexColor("#6B7280")
GRAY_200 = colors.HexColor("#E5E7EB")
WHITE = colors.white


def _status_color(status: str) -> colors.Color:
    if status == "pass":
        return GREEN
    if status == "warning":
        return YELLOW
    return RED


def _status_bg(status: str) -> colors.Color:
    if status == "pass":
        return GREEN_BG
    if status == "warning":
        return YELLOW_BG
    return RED_BG


def _status_icon(status: str) -> str:
    if status == "pass":
        return "PASS"
    if status == "warning":
        return "WARN"
    return "FAIL"


def _score_color(score: int) -> colors.Color:
    if score >= 80:
        return GREEN
    if score >= 50:
        return YELLOW
    return RED


# ── Styles ──────────────────────────────────────────────────────────────

def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=28,
        textColor=BLUE_DARK,
        alignment=TA_CENTER,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontSize=14,
        textColor=GRAY_500,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=BLUE_DARK,
        spaceBefore=20,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        "SubSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=GRAY_700,
        spaceBefore=14,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        textColor=GRAY_700,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "ScoreValue",
        parent=styles["Normal"],
        fontSize=36,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "ScoreLabel",
        parent=styles["Normal"],
        fontSize=11,
        textColor=GRAY_500,
        alignment=TA_CENTER,
        spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        "Recommendation",
        parent=styles["Normal"],
        fontSize=10,
        textColor=GRAY_700,
        leftIndent=12,
        spaceAfter=4,
        bulletFontName="Helvetica",
        bulletFontSize=10,
    ))
    styles.add(ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GRAY_500,
        alignment=TA_CENTER,
    ))

    return styles


# ── PDF Generator ───────────────────────────────────────────────────────

def generate_compliance_pdf(
    compliance_data: dict,
    health_data: dict,
    project_name: str,
    project_code: str,
) -> BytesIO:
    """
    Generează un raport PDF complet ISO 19650 pentru un proiect.

    Args:
        compliance_data: rezultatul din check_full_compliance()
        health_data: rezultatul din compute_project_health()
        project_name: Numele proiectului
        project_code: Codul proiectului

    Returns:
        BytesIO buffer cu PDF-ul generat.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _get_styles()
    story: list = []
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    # ── Pagina de copertă ─────────────────────────────────────────────
    story.append(Spacer(1, 4 * cm))

    # Logo area
    story.append(Paragraph("Agent BIM Romania", styles["CoverTitle"]))
    story.append(Spacer(1, 0.5 * cm))

    # Blue separator line
    line_table = Table([[""]],colWidths=[14 * cm], rowHeights=[3 * mm])
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_DARK),
    ]))
    story.append(line_table)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Raport Conformitate ISO 19650", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"<b>{project_name}</b> ({project_code})",
        ParagraphStyle("CoverProject", parent=styles["Normal"], fontSize=16,
                        alignment=TA_CENTER, textColor=GRAY_700),
    ))
    story.append(Spacer(1, 1 * cm))

    # Overall score big number
    overall = compliance_data.get("overall_score", 0)
    score_style = ParagraphStyle(
        "BigScore", parent=styles["ScoreValue"],
        textColor=_score_color(overall),
    )
    story.append(Paragraph(f"<b>{overall}%</b>", score_style))
    story.append(Paragraph("Scor Overall Conformitate ISO 19650", styles["ScoreLabel"]))

    story.append(Spacer(1, 1 * cm))

    # Summary counts
    tc = compliance_data.get("total_checks", 0)
    pc = compliance_data.get("pass_count", 0)
    wc = compliance_data.get("warning_count", 0)
    fc = compliance_data.get("fail_count", 0)

    summary_data = [[
        Paragraph(f"<b>{tc}</b><br/>Total verificari", styles["BodyText2"]),
        Paragraph(f"<font color='#16A34A'><b>{pc}</b></font><br/>Pass", styles["BodyText2"]),
        Paragraph(f"<font color='#F59E0B'><b>{wc}</b></font><br/>Warning", styles["BodyText2"]),
        Paragraph(f"<font color='#EF4444'><b>{fc}</b></font><br/>Fail", styles["BodyText2"]),
    ]]
    summary_table = Table(summary_data, colWidths=[3.5 * cm] * 4)
    summary_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_200),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_200),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Generat: {now}", styles["Footer"]))

    story.append(PageBreak())

    # ── Sănătatea proiectului ─────────────────────────────────────────
    story.append(Paragraph("Sanatatea Proiectului", styles["SectionTitle"]))

    health_score = health_data.get("score", 0)
    h_color = _score_color(health_score)
    story.append(Paragraph(
        f"Scor sanatate: <font color='{h_color.hexval()}'><b>{health_score}%</b></font>",
        styles["SubSection"],
    ))

    # Health details table
    h_details = [
        ["Componenta", "Status"],
        ["BEP generat", "Da" if health_data.get("has_bep") else "Nu"],
        ["Model IFC", "Da" if health_data.get("has_ifc") else "Nu"],
        ["Verificare BEP", "Da" if health_data.get("has_verification") else "Nu"],
        ["EIR definit", "Da" if health_data.get("has_eir") else "Nu"],
        ["RACI definit", "Da" if health_data.get("has_raci") else "Nu"],
        ["Plan securitate", "Da" if health_data.get("has_security_plan") else "Nu"],
        ["TIDP completare", f"{health_data.get('tidp_completion', 0)}%"],
        ["Clash-uri deschise", str(health_data.get("clash_open_count", 0))],
    ]
    h_table = Table(h_details, colWidths=[8 * cm, 5 * cm])
    h_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_200),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_200),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(h_table)

    # Alerts
    alerts = health_data.get("alerts", [])
    if alerts:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Alerte", styles["SubSection"]))
        for alert in alerts:
            story.append(Paragraph(
                f"<font color='#EF4444'>!</font>  {alert}",
                styles["Recommendation"],
            ))

    story.append(PageBreak())

    # ── Conformitate per parte ISO 19650 ──────────────────────────────
    story.append(Paragraph("Conformitate ISO 19650 — Detalii per Parte", styles["SectionTitle"]))

    parts = compliance_data.get("parts", {})

    # Score summary table for all parts
    part_summary = [["Parte ISO 19650", "Scor"]]
    for part_key in ["iso_19650_1", "iso_19650_2", "iso_19650_3", "iso_19650_5"]:
        part = parts.get(part_key, {})
        title = part.get("title", part_key)
        score = part.get("score", 0)
        part_summary.append([title, f"{score}%"])

    ps_table = Table(part_summary, colWidths=[11 * cm, 3 * cm])
    ps_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_200),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_200),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(ps_table)
    story.append(Spacer(1, 0.5 * cm))

    # Detailed checks per part
    for part_key in ["iso_19650_1", "iso_19650_2", "iso_19650_3", "iso_19650_5"]:
        part = parts.get(part_key, {})
        title = part.get("title", part_key)
        score = part.get("score", 0)
        checks = part.get("checks", [])

        story.append(Paragraph(
            f"{title} — <font color='{_score_color(score).hexval()}'>{score}%</font>",
            styles["SubSection"],
        ))

        if checks:
            check_data = [["Verificare", "Status"]]
            for ch in checks:
                status = ch.get("status", "fail")
                check_data.append([
                    ch.get("check", ""),
                    _status_icon(status),
                ])

            ct = Table(check_data, colWidths=[11 * cm, 3 * cm])

            # Build row-specific styles for status coloring
            table_style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.5, GRAY_200),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_200),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]

            for i, ch in enumerate(checks, start=1):
                status = ch.get("status", "fail")
                table_style_cmds.append(
                    ("TEXTCOLOR", (1, i), (1, i), _status_color(status))
                )
                table_style_cmds.append(
                    ("FONTNAME", (1, i), (1, i), "Helvetica-Bold")
                )

            ct.setStyle(TableStyle(table_style_cmds))
            story.append(ct)

        story.append(Spacer(1, 0.3 * cm))

    # ── Recomandări ───────────────────────────────────────────────────
    recommendations = compliance_data.get("recommendations", [])
    if recommendations:
        story.append(PageBreak())
        story.append(Paragraph("Recomandari", styles["SectionTitle"]))
        story.append(Paragraph(
            "Pentru a imbunatati conformitatea ISO 19650, urmatoarele actiuni sunt recomandate:",
            styles["BodyText2"],
        ))
        story.append(Spacer(1, 0.3 * cm))

        for i, rec in enumerate(recommendations, start=1):
            story.append(Paragraph(
                f"<b>{i}.</b>  {rec}",
                styles["Recommendation"],
            ))

    # ── Footer ────────────────────────────────────────────────────────
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        f"Agent BIM Romania — Raport generat automat la {now}",
        styles["Footer"],
    ))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
