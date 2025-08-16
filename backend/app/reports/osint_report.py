from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table


def build_osint_report(subject: dict[str, Any], plan: list[dict[str, Any]], summary: dict[str, Any] | None = None) -> bytes:
    """Create a compact OSINT PDF report with subject, plan, and summary (entities/timeline)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("OSINT Dossier", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    # Subject summary
    story.append(Paragraph("Subject", styles["Heading2"]))
    subj_lines = []
    for k, v in (subject or {}).items():
        subj_lines.append(f"<b>{k}:</b> {v}")
    if not subj_lines:
        subj_lines.append("No subject fields provided.")
    for line in subj_lines:
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    # Plan table
    story.append(Paragraph("Planned Collection Steps", styles["Heading2"]))
    data = [["#", "Platform", "Query"]]
    for i, step in enumerate(plan or [], start=1):
        data.append([str(i), str(step.get("platform", "")), str(step.get("query", ""))])
    table = Table(data, colWidths=[0.4 * inch, 1.6 * inch, 4.0 * inch])
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    # Summary: entities
    if summary:
        ents = list(map(str, (summary or {}).get("entities", []) or []))
        story.append(Paragraph("Extracted Entities", styles["Heading2"]))
        if ents:
            # Render in a compact multi-column-like table
            rows: list[list[str]] = []
            row: list[str] = []
            for i, e in enumerate(ents[:60], start=1):
                row.append(e)
                if len(row) == 3:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            story.append(Table(rows))
        else:
            story.append(Paragraph("No entities found.", styles["Normal"]))

        # Summary: timeline
        tl = (summary or {}).get("timeline", []) or []
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Timeline (heuristic)", styles["Heading2"]))
        if tl:
            tdata = [["Date", "Context"]]
            for ev in tl[:20]:
                tdata.append([str(ev.get("date_text", "")), str((ev.get("context", "") or "")[:100])])
            story.append(Table(tdata, colWidths=[1.6 * inch, 4.4 * inch]))
        else:
            story.append(Paragraph("No timeline events detected.", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()


