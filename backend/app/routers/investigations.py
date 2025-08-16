from __future__ import annotations

import uuid
from datetime import UTC
from typing import Any

from app.agent.celery_app import celery_app
from app.db import SessionLocal
from app.middleware.auth import validate_api_key
from app.tasks.investigation_tasks import (
    run_apt_attribution,
    run_finance_triage,
    run_forensics_timeline,
    run_investigations_autopilot,
    run_malware_dynamic,
    run_osint_dossier,
    run_sca_scan,
)
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import Response, StreamingResponse

router = APIRouter(prefix="/investigations", tags=["investigations"], dependencies=[Depends(validate_api_key)])


@router.post("/osint/run")
def start_osint(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    data = dict(payload or {})
    try:
        job = run_osint_dossier.delay({**data, "task_id": None})
        _record("osint", job.id, payload)
        return {"status": "queued", "task_id": job.id}
    except Exception:
        # Fallback to synchronous execution if broker is unavailable
        result = run_osint_dossier.apply(args=[{**data, "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("osint", tid, payload)
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}


@router.post("/finance/run")
def start_finance(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    try:
        job = run_finance_triage.delay({**(payload or {}), "task_id": None})
        _record("finance", job.id, payload)
        return {"status": "queued", "task_id": job.id}
    except Exception:
        result = run_finance_triage.apply(args=[{**(payload or {}), "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("finance", tid, payload)
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}


@router.post("/autopilot/run")
def start_autopilot(payload: dict[str, Any] | None = None, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    try:
        job = run_investigations_autopilot.delay({**(payload or {}), "task_id": None})
        _record("autopilot", job.id, payload or {})
        return {"status": "queued", "task_id": job.id}
    except Exception:
        result = run_investigations_autopilot.apply(args=[{**(payload or {}), "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("autopilot", tid, payload or {})
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}
@router.post("/forensics/timeline/run")
def start_forensics_timeline(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    try:
        job = run_forensics_timeline.delay({**(payload or {}), "task_id": None})
        _record("forensics_timeline", job.id, payload)
        return {"status": "queued", "task_id": job.id}
    except Exception:
        result = run_forensics_timeline.apply(args=[{**(payload or {}), "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("forensics_timeline", tid, payload)
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}


@router.post("/malware/dynamic/run")
def start_malware_dynamic(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    try:
        job = run_malware_dynamic.delay({**(payload or {}), "task_id": None})
        _record("malware_dynamic", job.id, payload)
        return {"status": "queued", "task_id": job.id}
    except Exception:
        result = run_malware_dynamic.apply(args=[{**(payload or {}), "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("malware_dynamic", tid, payload)
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}


@router.post("/threat/apt_attribution/run")
def start_apt_attribution(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    try:
        job = run_apt_attribution.delay({**(payload or {}), "task_id": None})
        _record("apt_attribution", job.id, payload)
        return {"status": "queued", "task_id": job.id}
    except Exception:
        result = run_apt_attribution.apply(args=[{**(payload or {}), "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("apt_attribution", tid, payload)
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}


@router.post("/supplychain/sca/run")
def start_sca(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _enforce_api_key(x_api_key)
    try:
        job = run_sca_scan.delay({**(payload or {}), "task_id": None})
        _record("sca_scan", job.id, payload)
        return {"status": "queued", "task_id": job.id}
    except Exception:
        result = run_sca_scan.apply(args=[{**(payload or {}), "task_id": None}]).result
        tid = str(uuid.uuid4())
        _record("sca_scan", tid, payload)
        _update(tid, "completed", result)
        return {"status": "completed", "task_id": tid, "result": result}


@router.get("/recent")
def recent(limit: int = 20) -> dict[str, Any]:
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
    import json as _json

    from app.models import InvestigationRun
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
    token = request.query_params.get("token")
    _enforce_api_key(token or x_api_key, read_only=True)
    async def event_generator():
        import asyncio as _aio
        import json as _json
        last_state: str | None = None
        while True:
            if await request.is_disconnected():
                break
            result = celery_app.AsyncResult(task_id)
            state = result.state
            payload: dict[str, Any] = {"task_id": task_id, "state": state}
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
    import json as _json

    from app.ai.investigation_planner import plan_osint
    from app.models import InvestigationRun

    db = SessionLocal()
    try:
        run = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id, InvestigationRun.kind == "osint").first()
        if not run:
            return Response(status_code=404)
        try:
            params = _json.loads(run.parameters_json or "{}")
            _sub = (params or {}).get("subject")
            subj: dict[str, Any] = _sub if isinstance(_sub, dict) else {}
        except Exception:
            subj = {}
        plan = plan_osint(subj)
        summary = None
        try:
            import json as __json
            summary = __json.loads(run.result_summary_json or "{}") if run.result_summary_json else None
        except Exception:
            summary = None
        # Lazy import report generator to avoid hard dependency in tests
        try:
            from app.reports.osint_report import build_osint_report  # type: ignore
            pdf_bytes = build_osint_report(subj, plan, summary)
            return Response(content=pdf_bytes, media_type="application/pdf")
        except Exception:
            # Report generator not available; return 501
            return Response(content=b"report generation not available", media_type="text/plain", status_code=501)
    finally:
        db.close()


@router.get("/forensics/report/{task_id}")
def get_forensics_report(task_id: str, x_api_key: str | None = Header(default=None)) -> Response:
    _enforce_api_key(x_api_key, read_only=True)
    import json as _json

    from app.models import InvestigationRun
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
    import json as _json

    from app.models import InvestigationRun
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
    import json as _json

    from app.models import InvestigationRun
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
    import json as _json

    from app.models import InvestigationRun
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
    import csv as _csv
    import json as _json
    from io import StringIO

    from app.models import InvestigationRun
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
    import json as _json

    from app.models import InvestigationRun
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
    import csv as _csv
    import json as _json
    from io import StringIO

    from app.models import InvestigationRun
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


def _record(kind: str, task_id: str, params: dict[str, Any], task_id_override: str | None = None) -> None:
    import json as _json

    from app.models import InvestigationRun
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


def _update(task_id: str, status: str, result_obj: dict[str, Any] | None) -> None:
    import json as _json

    from app.models import InvestigationRun
    db = SessionLocal()
    try:
        rec = db.query(InvestigationRun).filter(InvestigationRun.task_id == task_id).first()
        if rec:
            rec.status = status
            if result_obj is not None:
                rec.result_summary_json = _json.dumps(result_obj)
            from datetime import datetime
            rec.updated_at = datetime.now(UTC)
            db.add(rec)
            db.commit()
    finally:
        db.close()


def _enforce_api_key(x_api_key: str | None, read_only: bool = False) -> None:
    import os as _os
    from fastapi import HTTPException
    secure_mode = _os.getenv("SECURE_MODE", "false").lower() == "true"
    expected = _os.getenv("INTERNAL_API_KEY")
    if secure_mode:
        if not expected:
            raise HTTPException(status_code=500, detail="server not configured: api key missing")
        if not x_api_key:
            raise HTTPException(status_code=401, detail="X-API-Key header required")
        if x_api_key != expected:
            raise HTTPException(status_code=401, detail="invalid api key")
        return
    if expected:
        if not x_api_key or x_api_key != expected:
            raise HTTPException(status_code=401, detail="invalid or missing api key")
    # When no expected key and not secure, allow


