from __future__ import annotations

from io import BytesIO
from typing import Any, Dict
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def build_forensics_report(summary: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Forensics Timeline Report", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    stats = (summary or {}).get("stats", {})
    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(f"Total events: {stats.get('total_events', 0)}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    events = (summary or {}).get("sample", [])
    story.append(Paragraph("Sample Events", styles["Heading2"]))
    data = [["Timestamp", "Event", "Context"]]
    for ev in events[:20]:
        data.append([str(ev.get("timestamp", "")), str(ev.get("event", "")), str(ev.get("path", ev.get("url", "")))])
    story.append(Table(data, colWidths=[2.0 * inch, 1.5 * inch, 3.0 * inch]))

    doc.build(story)
    return buf.getvalue()


