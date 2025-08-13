from __future__ import annotations

from typing import Any, Dict, List

from celery import shared_task
from app.ai.investigation_planner import plan_osint
from app.collectors.osint_collectors import get_collectors
from app.db import SessionLocal
from app.core.single_user import get_or_create_single_user
from app.ai.system_brain import plan_investigations
from app.operator.web_metrics import (
    automation_tasks_started as web_automation_tasks_started,
    automation_tasks_completed as web_automation_tasks_completed,
    automation_actions_total as web_automation_actions_total,
    automation_action_errors_total as web_automation_action_errors_total,
    automation_task_duration_s as web_automation_task_duration_s,
)


@shared_task(bind=True, name="investigation.osint.run")
def run_osint_dossier(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    import time
    start_t = time.time()
    try:
        web_automation_tasks_started.inc()
    except Exception:
        pass
    # Planner → steps; collectors would run next (future)
    subject = (task_data or {}).get("subject") or {}
    steps = plan_osint(subject)
    # Attempt lightweight collection (headless) when enabled
    gathered: Dict[str, Any] = {"platforms": {}}
    try:
        import asyncio

        async def _run_collect() -> None:
            for step in steps:
                platform = step.get("platform")
                query = step.get("query") or ""
                for collector in get_collectors():
                    if collector.platform == platform:
                        items = await collector.collect(query)
                        gathered.setdefault("platforms", {}).setdefault(platform, []).extend(items)
                        try:
                            web_automation_actions_total.inc()
                        except Exception:
                            pass

        asyncio.run(_run_collect())
    except Exception:
        pass

    # Lightweight entity extraction and timeline heuristics (no heavy deps)
    import re

    email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    phone_re = re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)[\s.-]?)?\d{3}[\s.-]?\d{2,4}[\s.-]?\d{2,4}\b")
    url_re = re.compile(r"https?://[^\s]+")
    # Dates like 2024-05-21, 05/21/2024, 21 May 2024
    date_re = re.compile(
        r"\b((?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2})|(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})|(?:\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{2,4}))\b",
        re.IGNORECASE,
    )

    def _candidate_names(text: str) -> List[str]:
        names: List[str] = []
        # Sequences of 2-3 capitalized words
        for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", text):
            names.append(m.group(1))
        return names

    entity_set: set[str] = set()
    timeline: List[Dict[str, Any]] = []
    for plist in gathered.get("platforms", {}).values():
        for it in plist:
            text = (it.get("text") or it.get("url") or "").strip()
            if not text:
                continue
            for m in email_re.findall(text):
                entity_set.add(m)
            for m in phone_re.findall(text):
                entity_set.add(m)
            for m in url_re.findall(text):
                entity_set.add(m)
            for nm in _candidate_names(text):
                entity_set.add(nm)
            for dm in date_re.findall(text):
                timeline.append({"date_text": dm if isinstance(dm, str) else dm[0], "context": text[:200]})

    entities = sorted(list(entity_set))[:200]
    # Deduplicate timeline by (date_text, context)
    seen_tl: set[tuple[str, str]] = set()
    unique_timeline: List[Dict[str, Any]] = []
    for ev in timeline:
        key = (ev.get("date_text", ""), ev.get("context", ""))
        if key in seen_tl:
            continue
        seen_tl.add(key)
        unique_timeline.append(ev)
    timeline = unique_timeline[:100]

    result = {
        "success": True,
        "subject": subject,
        "plan": steps,
        "sources": gathered,
        "entities": entities,
        "timeline": timeline,
        "graph": {"nodes": [], "edges": []},
        "notes": "OSINT scaffold executed",
    }

    # Persist summary back to InvestigationRun (best-effort) under single user context
    try:
        from app.models import InvestigationRun
        import json as _json
        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None) or task_data.get("task_id")
            if task_id:
                rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
                if rec:
                    rec.status = "completed"
                    rec.result_summary_json = _json.dumps({
                        "entities": entities,
                        "platforms": list(gathered.get("platforms", {}).keys()),
                        "timeline": timeline,
                    })
                    db.add(rec)
                    db.commit()
        finally:
            db.close()
    except Exception:
        pass

    try:
        web_automation_tasks_completed.inc()
        web_automation_task_duration_s.observe(max(0.0, time.time() - start_t))
    except Exception:
        pass
    return result


@shared_task(bind=True, name="investigation.finance.run")
def run_finance_triage(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder: accept CSV reference (already uploaded) and produce triage
    return {
        "success": True,
        "summary": {"total_transactions": 0, "red_flags": []},
        "notes": "Finance scaffold executed",
    }


# Forensics: timeline extraction scaffold (Plaso/Timesketch placeholders)
@shared_task(bind=True, name="investigation.forensics.timeline.run")
def run_forensics_timeline(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    source = (task_data or {}).get("source") or "evidence.dd"
    # Placeholder processing summary
    events: List[Dict[str, Any]] = [
        {"timestamp": "2024-01-10T12:00:00Z", "event": "File Created", "path": "/Users/jdoe/Documents/a.docx"},
        {"timestamp": "2024-01-11T08:15:12Z", "event": "Browser History", "url": "https://example.com/login"},
    ]
    result = {
        "success": True,
        "source": source,
        "events": events,
        "stats": {"total_events": len(events)},
        "notes": "Forensics timeline scaffold executed (Plaso/Timesketch not invoked)",
    }
    # Persist summary
    try:
        from app.models import InvestigationRun
        import json as _json
        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None) or task_data.get("task_id")
            if task_id:
                rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
                if rec:
                    rec.status = "completed"
                    rec.result_summary_json = _json.dumps({"stats": result["stats"], "sample": events[:5]})
                    db.add(rec)
                    db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return result


# Malware: dynamic analysis scaffold (Cuckoo/VMRay placeholders)
@shared_task(bind=True, name="investigation.malware.dynamic.run")
def run_malware_dynamic(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    sample_ref = (task_data or {}).get("sample") or "sample.exe"
    iocs = {
        "domains": ["cnc.bad.example"],
        "ips": ["10.0.0.66"],
        "mutexes": ["Global\\MalwareLock"],
        "registry_keys": ["HKCU\\Software\\BadKey"],
    }
    mitre = [
        {"technique": "T1059", "name": "Command and Scripting Interpreter"},
        {"technique": "T1105", "name": "Ingress Tool Transfer"},
    ]
    result = {
        "success": True,
        "sample": sample_ref,
        "summary": {"score": 6.5, "severity": "medium"},
        "iocs": iocs,
        "mitre": mitre,
        "notes": "Malware dynamic analysis scaffold executed (sandbox not invoked)",
    }
    try:
        from app.models import InvestigationRun
        import json as _json
        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None) or task_data.get("task_id")
            if task_id:
                rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
                if rec:
                    rec.status = "completed"
                    rec.result_summary_json = _json.dumps({"score": 6.5, "iocs": iocs})
                    db.add(rec)
                    db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return result


# Threat intel: simple APT attribution scoring scaffold
@shared_task(bind=True, name="investigation.threat.apt_attribution.run")
def run_apt_attribution(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    evidence = (task_data or {}).get("evidence") or {}
    groups = (task_data or {}).get("candidate_groups") or ["APT28", "APT29", "APT1"]

    def _score(group: str) -> float:
        base = {
            "APT28": 0.72,
            "APT29": 0.68,
            "APT1": 0.55,
        }.get(group, 0.4)
        # Nudge by presence of categories
        weights = {"infrastructure": 0.3, "malware": 0.25, "tactics": 0.2, "targets": 0.15, "timing": 0.1}
        bonus = 0.0
        for cat, w in weights.items():
            if evidence.get(cat):
                bonus += 0.15 * w
        return min(base + bonus, 0.98)

    results = [{"group": g, "confidence": round(_score(g) * 100, 2)} for g in groups]
    results.sort(key=lambda x: x["confidence"], reverse=True)
    # Persist lightweight summary
    try:
        from app.models import InvestigationRun
        import json as _json
        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None) or task_data.get("task_id")
            if task_id:
                rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
                if rec:
                    rec.status = "completed"
                    rec.result_summary_json = _json.dumps({"top": results[:3]})
                    db.add(rec)
                    db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return {"success": True, "results": results, "notes": "APT attribution scaffold executed"}


# Supply chain security: SCA scan scaffold (Snyk/FOSSA placeholders)
@shared_task(bind=True, name="investigation.supplychain.sca.run")
def run_sca_scan(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    project = (task_data or {}).get("project") or "backend/"
    findings = [
        {"package": "requests", "version": "2.19.0", "cve": "CVE-2018-18074", "severity": "high"},
    ]
    # Persist summary
    try:
        from app.models import InvestigationRun
        import json as _json
        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None) or task_data.get("task_id")
            if task_id:
                rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
                if rec:
                    rec.status = "completed"
                    rec.result_summary_json = _json.dumps({"findings": findings[:5]})
                    db.add(rec)
                    db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return {"success": True, "project": project, "findings": findings, "notes": "SCA scan scaffold executed"}


# Autopilot orchestrator: run OSINT → Forensics → Malware → APT → SCA and aggregate
@shared_task(bind=True, name="investigation.autopilot.run")
def run_investigations_autopilot(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    subject = (task_data or {}).get("subject") or {"name": "Jane Doe"}
    context = {k: v for k, v in (task_data or {}).items() if k != "subject"}
    plan = plan_investigations(context)
    results: Dict[str, Any] = {"subject": subject, "plan": plan, "steps": []}

    for step in plan:
        kind = step.get("kind")
        if kind == "osint":
            res = run_osint_dossier.apply(args=[{"subject": subject, "task_id": None}]).result
            results["steps"].append({"osint": res})
        elif kind == "forensics_timeline":
            res = run_forensics_timeline.apply(args=[{"source": context.get("forensics_source", "evidence.dd"), "task_id": None}]).result
            results["steps"].append({"forensics_timeline": res})
        elif kind == "malware_dynamic":
            res = run_malware_dynamic.apply(args=[{"sample": context.get("malware_sample", "sample.exe"), "task_id": None}]).result
            results["steps"].append({"malware_dynamic": res})
        elif kind == "apt_attribution":
            res = run_apt_attribution.apply(args=[{"candidate_groups": ["APT28", "APT29", "APT1"], "evidence": {"infrastructure": True}, "task_id": None}]).result
            results["steps"].append({"apt_attribution": res})
        elif kind == "sca":
            res = run_sca_scan.apply(args=[{"project": context.get("project_path", "backend/"), "task_id": None}]).result
            results["steps"].append({"sca": res})

    results["success"] = True
    results["notes"] = "Autopilot orchestrated run completed"

    # Persist back to InvestigationRun if a task id exists (synchronous apply() returns result only)
    try:
        from app.models import InvestigationRun
        import json as _json
        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None) or task_data.get("task_id")
            if task_id:
                rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
                if rec:
                    rec.status = "completed"
                    rec.result_summary_json = _json.dumps(results)
                    db.add(rec)
                    db.commit()
                    # Optional: notify via integrations if configured
                    try:
                        import os
                        if os.getenv("AUTOPILOT_NOTIFY_EMAIL_TO"):
                            from app.integrations.router import hub
                            to_addr = os.getenv("AUTOPILOT_NOTIFY_EMAIL_TO")
                            subj = "Autopilot Investigation Completed"
                            body = "Autopilot completed with steps: " + ", ".join([list(s.keys())[0] for s in results.get("steps", [])])
                            # Use mock gmail if real not configured
                            integ = hub.integrations.get("gmail")
                            if integ:
                                try:
                                    import asyncio
                                    asyncio.get_event_loop().run_until_complete(integ.send_email("1", to_addr, subj, body))  # type: ignore[attr-defined]
                                except Exception:
                                    pass
                    except Exception:
                        pass
        finally:
            db.close()
    except Exception:
        pass
    return results


