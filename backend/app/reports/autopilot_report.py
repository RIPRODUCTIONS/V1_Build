from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table


def build_autopilot_report(summary: dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    story: list[Any] = []

    story.append(Paragraph("Investigations Autopilot Report", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    subject = (summary or {}).get("subject", {})
    plan = (summary or {}).get("plan", [])
    steps = (summary or {}).get("steps", [])

    story.append(Paragraph("Subject", styles["Heading2"]))
    if subject:
        for k, v in subject.items():
            story.append(Paragraph(f"<b>{k}:</b> {v}", styles["Normal"]))
    else:
        story.append(Paragraph("No subject provided.", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Plan", styles["Heading2"]))
    table = Table([["#", "Kind"]] + [[str(i + 1), str(s.get("kind", ""))] for i, s in enumerate(plan)], colWidths=[0.4 * inch, 2.0 * inch])
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    # Extract OSINT entities/timeline
    osint = None
    for s in steps:
        if "osint" in s:
            osint = s["osint"]
            break
    entities = list(map(str, (osint or {}).get("entities", []) or [])) if osint else []
    timeline = (osint or {}).get("timeline", []) if osint else []

    story.append(Paragraph("Extracted Entities", styles["Heading2"]))
    if entities:
        rows: list[list[str]] = []
        row: list[str] = []
        for _i, e in enumerate(entities[:60], start=1):
            row.append(e)
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        story.append(Table(rows))
    else:
        story.append(Paragraph("None.", styles["Normal"]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Timeline (heuristic)", styles["Heading2"]))
    if timeline:
        tdata = [["Date", "Context"]]
        for ev in timeline[:20]:
            tdata.append([str(ev.get("date_text", "")), str((ev.get("context", "") or "")[:100])])
        story.append(Table(tdata, colWidths=[1.6 * inch, 4.4 * inch]))
    else:
        story.append(Paragraph("No timeline events detected.", styles["Normal"]))

    # Malware IOCs if present
    malware = None
    for s in steps:
        if "malware_dynamic" in s:
            malware = s["malware_dynamic"]
            break
    if malware:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Malware IOCs", styles["Heading2"]))
        iocs = malware.get("iocs", {})
        rows = [["Type", "Value"]]
        for k in ("domains", "ips", "mutexes", "registry_keys"):
            for v in iocs.get(k, [])[:20]:
                rows.append([k, str(v)])
        story.append(Table(rows, colWidths=[1.6 * inch, 4.4 * inch]))

    doc.build(story)
    return buf.getvalue()


