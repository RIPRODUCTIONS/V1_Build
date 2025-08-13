from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request, Header
from fastapi.responses import Response, StreamingResponse

from app.db import SessionLocal
from app.tasks.investigation_tasks import (
    run_osint_dossier,
    run_finance_triage,
    run_forensics_timeline,
    run_malware_dynamic,
    run_apt_attribution,
    run_sca_scan,
    run_investigations_autopilot,
)
from app.agent.celery_app import celery_app


router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("/osint/run")
def start_osint(payload: Dict[str, Any], x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    data = dict(payload or {})
    # Attach task_id later in Celery; for now, pass None; persistence updated on completion when task reports back
    job = run_osint_dossier.delay({**data, "task_id": None})
    _record("osint", job.id, payload, task_id=job.id)
    return {"status": "queued", "task_id": job.id}


@router.post("/finance/run")
def start_finance(payload: Dict[str, Any], x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    job = run_finance_triage.delay({**(payload or {}), "task_id": None})
    _record("finance", job.id, payload, task_id=job.id)
    return {"status": "queued", "task_id": job.id}


@router.post("/autopilot/run")
def start_autopilot(payload: Dict[str, Any] | None = None, x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    job = run_investigations_autopilot.delay({**(payload or {}), "task_id": None})
    _record("autopilot", job.id, payload or {}, task_id=job.id)
    return {"status": "queued", "task_id": job.id}
@router.post("/forensics/timeline/run")
def start_forensics_timeline(payload: Dict[str, Any], x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    job = run_forensics_timeline.delay({**(payload or {}), "task_id": None})
    _record("forensics_timeline", job.id, payload, task_id=job.id)
    return {"status": "queued", "task_id": job.id}


@router.post("/malware/dynamic/run")
def start_malware_dynamic(payload: Dict[str, Any], x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    job = run_malware_dynamic.delay({**(payload or {}), "task_id": None})
    _record("malware_dynamic", job.id, payload, task_id=job.id)
    return {"status": "queued", "task_id": job.id}


@router.post("/threat/apt_attribution/run")
def start_apt_attribution(payload: Dict[str, Any], x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    job = run_apt_attribution.delay({**(payload or {}), "task_id": None})
    _record("apt_attribution", job.id, payload, task_id=job.id)
    return {"status": "queued", "task_id": job.id}


@router.post("/supplychain/sca/run")
def start_sca(payload: Dict[str, Any], x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    _enforce_api_key(x_api_key)
    job = run_sca_scan.delay({**(payload or {}), "task_id": None})
    _record("sca_scan", job.id, payload, task_id=job.id)
    return {"status": "queued", "task_id": job.id}


@router.get("/recent")
def recent(limit: int = 20) -> Dict[str, Any]:
    from app.models import InvestigationRun

    db = SessionLocal()
    try:
        rows = (
            db.query(InvestigationRun)
            .order_by(InvestigationRun.created_at.desc())
            .limit(max(1, min(100, limit)))
            .all()
        )
        return {
            "items": [
                {
                    "id": r.id,
                    "task_id": r.task_id,
                    "kind": r.kind,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.get("/{task_id}", response_model=None)
def get_investigation(task_id: str, x_api_key: str | None = Header(default=None)):
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
        if not rec:
            return Response(status_code=404)
        out = {
            "task_id": task_id,
            "kind": rec.kind,
            "status": rec.status,
            "parameters": None,
            "result_summary": None,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        }
        try:
            out["parameters"] = _json.loads(rec.parameters_json or "{}")
        except Exception:
            pass
        try:
            out["result_summary"] = _json.loads(rec.result_summary_json or "{}")
        except Exception:
            pass
        return out
    finally:
        db.close()


@router.get("/stream/{task_id}")
async def stream_investigation(task_id: str, request: Request, x_api_key: str | None = Header(default=None)) -> StreamingResponse:
    _enforce_api_key(x_api_key, read_only=True)
    async def event_generator():
        import json as _json
        import asyncio as _aio
        last_state: str | None = None
        while True:
            if await request.is_disconnected():
                break
            result = celery_app.AsyncResult(task_id)
            state = result.state
            payload: Dict[str, Any] = {"task_id": task_id, "state": state}
            status = "pending"
            if state == "SUCCESS":
                try:
                    _res = result.get(timeout=0)
                    payload["result"] = _res
                    _update(task_id, "completed", _res)
                except Exception as exc:
                    payload["error"] = str(exc)
                status = "completed"
            elif state in {"FAILURE", "REVOKED"}:
                try:
                    payload["error"] = str(result.result)
                except Exception:
                    pass
                status = "error"
                _update(task_id, "error", {"error": payload.get("error")})
            payload["status"] = status
            if state != last_state or status in {"completed", "error"}:
                yield f"data: {_json.dumps(payload)}\n\n"
                last_state = state
            if status in {"completed", "error"}:
                break
            await _aio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/osint/report/{task_id}")
def get_osint_report(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    # Minimal: synthesize from stored parameters and current plan re-run for the PDF
    # In a full implementation, we would persist the full result and render from that
    from app.ai.investigation_planner import plan_osint
    from app.models import InvestigationRun
    import json as _json

    db = SessionLocal()
    try:
        run = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "osint").first()
        if not run:
            return Response(status_code=404)
        subject = {}
        try:
            params = _json.loads(run.parameters_json or "{}")
            subject = (params or {}).get("subject") or {}
        except Exception:
            subject = {}
        plan = plan_osint(subject)
        summary = None
        try:
            import json as __json
            summary = __json.loads(run.result_summary_json or "{}") if run.result_summary_json else None
        except Exception:
            summary = None
        # Lazy import report generator to avoid hard dependency in tests
        try:
            from app.reports.osint_report import build_osint_report  # type: ignore
            pdf_bytes = build_osint_report(subject, plan, summary)
            return Response(content=pdf_bytes, media_type="application/pdf")
        except Exception:
            # Report generator not available; return 501
            return Response(content=b"report generation not available", media_type="text/plain", status_code=501)
    finally:
        db.close()


@router.get("/forensics/report/{task_id}")
def get_forensics_report(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        run = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "forensics_timeline").first()
        if not run:
            return Response(status_code=404)
        summary = None
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else None
        except Exception:
            summary = None
        try:
            from app.reports.forensics_report import build_forensics_report  # type: ignore
            pdf_bytes = build_forensics_report(summary or {})
            return Response(content=pdf_bytes, media_type="application/pdf")
        except Exception:
            return Response(content=b"report generation not available", media_type="text/plain", status_code=501)
    finally:
        db.close()


@router.get("/malware/report/{task_id}")
def get_malware_report(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        run = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "malware_dynamic").first()
        if not run:
            return Response(status_code=404)
        summary = None
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else None
        except Exception:
            summary = None
        try:
            from app.reports.malware_report import build_malware_report  # type: ignore
            pdf_bytes = build_malware_report(summary or {})
            return Response(content=pdf_bytes, media_type="application/pdf")
        except Exception:
            return Response(content=b"report generation not available", media_type="text/plain", status_code=501)
    finally:
        db.close()


@router.get("/autopilot/report/{task_id}")
def get_autopilot_report(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        run = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "autopilot").first()
        if not run:
            return Response(status_code=404)
        summary = None
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else None
        except Exception:
            summary = None
        try:
            from app.reports.autopilot_report import build_autopilot_report  # type: ignore
            pdf_bytes = build_autopilot_report(summary or {})
            return Response(content=pdf_bytes, media_type="application/pdf")
        except Exception:
            return Response(content=b"report generation not available", media_type="text/plain", status_code=501)
    finally:
        db.close()


# Artifact downloads (JSON/CSV) derived from stored InvestigationRun summaries
@router.get("/osint/entities/{task_id}.json")
def get_osint_entities_json(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        run = (
            db.query(InvestigationRun)
            .filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "osint")
            .first()
        )
        if not run:
            return Response(status_code=404)
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else {}
        except Exception:
            summary = {}
        data = _json.dumps({"entities": summary.get("entities", [])}).encode()
        return Response(content=data, media_type="application/json")
    finally:
        db.close()


@router.get("/osint/timeline/{task_id}.csv")
def get_osint_timeline_csv(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    from io import StringIO
    import csv as _csv
    db = SessionLocal()
    try:
        run = (
            db.query(InvestigationRun)
            .filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "osint")
            .first()
        )
        if not run:
            return Response(status_code=404)
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else {}
        except Exception:
            summary = {}
        rows = summary.get("timeline", []) or []
        buf = StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["date_text", "context"])
        for ev in rows:
            writer.writerow([ev.get("date_text", ""), (ev.get("context", "") or "")])
        return Response(content=buf.getvalue().encode(), media_type="text/csv")
    finally:
        db.close()


@router.get("/malware/iocs/{task_id}.json")
def get_malware_iocs_json(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        run = (
            db.query(InvestigationRun)
            .filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "malware_dynamic")
            .first()
        )
        if not run:
            return Response(status_code=404)
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else {}
        except Exception:
            summary = {}
        data = _json.dumps({"iocs": summary.get("iocs", summary.get("findings", {}))}).encode()
        return Response(content=data, media_type="application/json")
    finally:
        db.close()


@router.get("/forensics/events/{task_id}.csv")
def get_forensics_events_csv(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    from app.models import InvestigationRun
    import json as _json
    from io import StringIO
    import csv as _csv
    db = SessionLocal()
    try:
        run = (
            db.query(InvestigationRun)
            .filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "forensics_timeline")
            .first()
        )
        if not run:
            return Response(status_code=404)
        try:
            summary = _json.loads(run.result_summary_json or "{}") if run.result_summary_json else {}
        except Exception:
            summary = {}
        rows = summary.get("sample", []) or []
        buf = StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["timestamp", "event", "path", "url"])
        for ev in rows:
            writer.writerow([ev.get("timestamp", ""), ev.get("event", ""), ev.get("path", ""), ev.get("url", "")])
        return Response(content=buf.getvalue().encode(), media_type="text/csv")
    finally:
        db.close()


def _record(kind: str, task_id: str, params: Dict[str, Any], task_id_override: str | None = None) -> None:
    from app.models import InvestigationRun
    import json as _json
    db = SessionLocal()
    try:
        rec = InvestigationRun(
            kind=kind,
            task_id=task_id_override or task_id,
            status="queued",
            parameters_json=_json.dumps(params or {}),
        )
        db.add(rec)
        db.commit()
    finally:
        db.close()


def _update(task_id: str, status: str, result_obj: Dict[str, Any] | None) -> None:
    from app.models import InvestigationRun
    import json as _json
    from datetime import datetime as _dt
    db = SessionLocal()
    try:
        rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
        if rec:
            rec.status = status
            if result_obj is not None:
                rec.result_summary_json = _json.dumps(result_obj)
            rec.updated_at = _dt.utcnow()
            db.add(rec)
            db.commit()
    finally:
        db.close()


def _enforce_api_key(x_api_key: str | None, read_only: bool = False) -> None:
    import os as _os
    if (_os.getenv("SECURE_MODE", "false").lower() == "true"):
        expected = _os.getenv("INTERNAL_API_KEY")
        if not expected or x_api_key != expected:
            # Late import to avoid FastAPI dependency at import time in tests
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="unauthorized")


