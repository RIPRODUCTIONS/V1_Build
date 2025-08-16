from __future__ import annotations

import csv
import io
import time
from datetime import UTC, datetime, timedelta

from app.db import SessionLocal
from app.models import TemplatePreset, TemplateUsage
from app.tasks.web_automation_tasks import execute_web_automation_task
from app.web_operator.template_library import AutomationTemplateLibrary
from fastapi import APIRouter, HTTPException, Query, Response

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("")
async def list_templates(category: str | None = Query(default=None)) -> dict:
    lib = AutomationTemplateLibrary()
    items = await lib.list_templates_by_category(category)
    return {"templates": items, "categories": await lib.categories()}


@router.get("/{template_id}")
async def get_template(template_id: str) -> dict:
    lib = AutomationTemplateLibrary()
    try:
        t = await lib.get_template(template_id)
        return t
    except KeyError as e:
        raise HTTPException(status_code=404, detail="template not found") from e


async def _queue_for_template(template_id: str, parameters: dict) -> dict:
    lib = AutomationTemplateLibrary()
    try:
        t = await lib.get_template(template_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="template not found") from e
    # Minimal wiring for contact form lead generator: queue one task per target site
    if template_id == "contact_form_lead_generator":
        targets = parameters.get("target_websites") or []
        if not isinstance(targets, list) or not targets:
            raise HTTPException(status_code=400, detail="target_websites required (list)")
        task_ids_cf: list[str] = []
        for url in targets[:10]:  # cap to protect CI
            job = execute_web_automation_task.delay({
                "description": f"contact_form: {parameters.get('contact_message_template', '')[:40]}",
                "url": url,
            })
            task_ids_cf.append(job.id)
        # Log usage
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_cf), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_cf}
    if template_id == "ecommerce_price_monitor":
        product_urls = parameters.get("product_urls") or []
        if not isinstance(product_urls, list) or not product_urls:
            raise HTTPException(status_code=400, detail="product_urls required (list)")
        task_ids_pm: list[str] = []
        for url in product_urls[:10]:
            job = execute_web_automation_task.delay({
                "description": "price_monitor",
                "url": url,
            })
            task_ids_pm.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_pm), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_pm}
    if template_id == "linkedin_lead_extractor":
        profile_urls = parameters.get("profile_urls") or []
        if not isinstance(profile_urls, list) or not profile_urls:
            raise HTTPException(status_code=400, detail="profile_urls required (list)")
        task_ids_li: list[str] = []
        for url in profile_urls[:10]:
            job = execute_web_automation_task.delay({
                "description": "linkedin_lead_extract",
                "url": url,
            })
            task_ids_li.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_li), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_li}
    if template_id == "ecommerce_price_spy":
        product_urls = parameters.get("product_urls") or []
        if not isinstance(product_urls, list) or not product_urls:
            raise HTTPException(status_code=400, detail="product_urls required (list)")
        task_ids_ps: list[str] = []
        for url in product_urls[:10]:
            job = execute_web_automation_task.delay({
                "description": "ecommerce_price_spy",
                "url": url,
            })
            task_ids_ps.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_ps), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_ps}
    if template_id == "social_media_lead_harvester":
        queries = parameters.get("queries") or []
        if not isinstance(queries, list) or not queries:
            raise HTTPException(status_code=400, detail="queries required (list)")
        # For MVP, create search URLs (Google) per query
        task_ids_sl: list[str] = []
        for q in queries[:10]:
            url = f"https://www.google.com/search?q={__import__('urllib.parse', fromlist=['parse']).quote_plus(str(q))}"
            job = execute_web_automation_task.delay({
                "description": "social_leads_search",
                "url": url,
            })
            task_ids_sl.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_sl), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_sl}
    if template_id == "job_board_auto_applier":
        job_queries = parameters.get("job_queries") or []
        if not isinstance(job_queries, list) or not job_queries:
            raise HTTPException(status_code=400, detail="job_queries required (list)")
        task_ids_jb: list[str] = []
        for q in job_queries[:10]:
            url = f"https://www.google.com/search?q={__import__('urllib.parse', fromlist=['parse']).quote_plus(str(q))}+site:indeed.com+OR+site:linkedin.com/jobs"
            job = execute_web_automation_task.delay({
                "description": "job_auto_apply",
                "url": url,
            })
            task_ids_jb.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_jb), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_jb}
    if template_id == "review_reputation_monitor":
        brand_terms = parameters.get("brand_terms") or []
        if not isinstance(brand_terms, list) or not brand_terms:
            raise HTTPException(status_code=400, detail="brand_terms required (list)")
        task_ids_rr: list[str] = []
        for term in brand_terms[:10]:
            url = f"https://www.google.com/search?q={__import__('urllib.parse', fromlist=['parse']).quote_plus(str(term))}+reviews+OR+site:yelp.com+OR+site:trustpilot.com"
            job = execute_web_automation_task.delay({
                "description": "review_monitor",
                "url": url,
            })
            task_ids_rr.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_rr), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_rr}
    if template_id == "website_change_monitor":
        pages = parameters.get("pages") or []
        if not isinstance(pages, list) or not pages:
            raise HTTPException(status_code=400, detail="pages required (list)")
        task_ids_wc: list[str] = []
        for url in pages[:10]:
            job = execute_web_automation_task.delay({
                "description": "website_change_monitor",
                "url": url,
            })
            task_ids_wc.append(job.id)
        try:
            db = SessionLocal()
            try:
                from json import dumps
                db.add(TemplateUsage(template_id=template_id, queued_tasks=len(task_ids_wc), success=True, parameters_json=dumps(parameters)))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass
        return {"status": "queued", "template": t["id"], "task_ids": task_ids_wc}
    return {"status": "accepted", "template": t["id"], "parameters": parameters}


@router.post("/{template_id}/deploy")
async def deploy_template(template_id: str, parameters: dict) -> dict:
    return await _queue_for_template(template_id, parameters)


@router.post("/{template_id}/rerun")
async def rerun_template(template_id: str, parameters: dict) -> dict:
    return await _queue_for_template(template_id, parameters)


@router.get("/{template_id}/presets")
async def list_presets(template_id: str) -> dict:
    db = SessionLocal()
    try:
        rows = (
            db.query(TemplatePreset)
            .filter(TemplatePreset.template_id == template_id)
            .order_by(TemplatePreset.created_at.desc())
            .all()
        )
        return {"items": [{"id": p.id, "name": p.name, "parameters": __import__("json").loads(p.parameters_json)} for p in rows]}
    finally:
        db.close()


class PresetIn(dict):
    ...


@router.post("/{template_id}/presets")
async def create_preset(template_id: str, preset: dict) -> dict:
    name = str(preset.get("name") or "Preset")
    params = preset.get("parameters") or {}
    db = SessionLocal()
    try:
        from json import dumps
        rec = TemplatePreset(template_id=template_id, name=name, parameters_json=dumps(params))
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return {"id": rec.id, "name": rec.name}
    finally:
        db.close()


@router.post("/{template_id}/presets/{preset_id}/run")
async def run_preset(template_id: str, preset_id: int) -> dict:
    db = SessionLocal()
    try:
        rec = db.get(TemplatePreset, int(preset_id))
        if not rec or rec.template_id != template_id:
            raise HTTPException(status_code=404, detail="preset not found")
        params = __import__("json").loads(rec.parameters_json)
        return await _queue_for_template(template_id, params)
    finally:
        db.close()


@router.post("/{template_id}/rerun_bulk")
async def rerun_bulk_failures(template_id: str, hours: int = 24, limit: int = 50) -> dict:
    """Re-run failed usages for a template within the past N hours.

    Caps limit to protect the system during replays.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=max(1, min(168, int(hours))))
        rows = (
            db.query(TemplateUsage)
            .filter(
                TemplateUsage.template_id == template_id,
                TemplateUsage.success.is_(False),
                TemplateUsage.created_at >= cutoff,
            )
            .order_by(TemplateUsage.created_at.desc())
            .limit(max(1, min(200, int(limit))))
            .all()
        )
        task_ids: list[str] = []
        for r in rows:
            params = {}
            try:
                if r.parameters_json:
                    params = __import__("json").loads(r.parameters_json)
            except Exception:
                params = {}
            res = await _queue_for_template(template_id, params)
            ids = res.get("task_ids") or []
            task_ids.extend(ids if isinstance(ids, list) else [])
        return {"replayed": len(rows), "task_ids": task_ids[:200]}
    finally:
        db.close()


@router.post("/{template_id}/presets/save_last_failed")
async def save_last_failed_as_preset(template_id: str, name: str | None = None) -> dict:
    db = SessionLocal()
    try:
        row = (
            db.query(TemplateUsage)
            .filter(TemplateUsage.template_id == template_id, TemplateUsage.success.is_(False))
            .order_by(TemplateUsage.created_at.desc())
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="no failed usage found")
        params = {}
        try:
            if row.parameters_json:
                params = __import__("json").loads(row.parameters_json)
        except Exception:
            params = {}
        from json import dumps
        rec = TemplatePreset(template_id=template_id, name=(name or "Last Failed"), parameters_json=dumps(params))
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return {"id": rec.id, "name": rec.name}
    finally:
        db.close()


@router.get("/usage/summary")
async def usage_summary(template_id: str, hours: int = 24, buckets: int = 12) -> dict:
    db = SessionLocal()
    try:
        hours = max(1, min(168, int(hours)))
        buckets = max(2, min(48, int(buckets)))
        # simple in-memory cache with 30s TTL
        key = (template_id, hours, buckets)
        now = time.time()
        cache: dict = getattr(usage_summary, "_cache", {})  # type: ignore[attr-defined]
        if cache:
            entry = cache.get(key)
            if entry and (now - entry[0] < 30.0):
                return entry[1]
        start = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)
        rows = (
            db.query(TemplateUsage)
            .filter(TemplateUsage.template_id == template_id, TemplateUsage.created_at >= start)
            .order_by(TemplateUsage.created_at.asc())
            .all()
        )
        bucket_width_s = (hours * 3600) / buckets
        series = [{"t": i, "success": 0, "failed": 0} for i in range(buckets)]
        for r in rows:
            idx = int(((r.created_at - start).total_seconds()) // bucket_width_s)
            if idx < 0:
                continue
            if idx >= buckets:
                idx = buckets - 1
            if bool(r.success):
                series[idx]["success"] += 1
            else:
                series[idx]["failed"] += 1
        result = {"template_id": template_id, "hours": hours, "buckets": buckets, "series": series}
        cache[key] = (now, result)
        usage_summary._cache = cache  # type: ignore[attr-defined]
        return result
    finally:
        db.close()


@router.get("/usage", response_model=None)
async def recent_template_usage(template_id: str | None = None, limit: int = 10, success: bool | None = None, format: str | None = None, hours: int | None = None):
    """Return recent template deployments across all templates or a specific one."""
    db = SessionLocal()
    try:
        q = db.query(TemplateUsage)
        if template_id:
            q = q.filter(TemplateUsage.template_id == template_id)
        if success is not None:
            q = q.filter(TemplateUsage.success.is_(bool(success)))
        if hours is not None:
            try:
                h = max(1, min(168, int(hours)))
                since = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=h)
                q = q.filter(TemplateUsage.created_at >= since)
            except Exception:
                pass
        rows = q.order_by(TemplateUsage.created_at.desc()).limit(max(1, min(200, int(limit)))).all()
        items = [
            {
                "template_id": r.template_id,
                "queued_tasks": r.queued_tasks,
                "success": bool(r.success),
                "created_at": r.created_at.isoformat(),
                "parameters": r.parameters_json and __import__("json").loads(r.parameters_json) or None,
            }
            for r in rows
        ]
        if (format or "").lower() == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=["template_id", "queued_tasks", "success", "created_at", "parameters"])
            writer.writeheader()
            for it in items:
                writer.writerow(it)
            data = buf.getvalue()
            return Response(content=data, media_type="text/csv", headers={
                "Content-Disposition": f"attachment; filename=template_usage{'_' + template_id if template_id else ''}.csv"
            })
        return {
            "items": [
                *items
            ]
        }
    finally:
        db.close()


