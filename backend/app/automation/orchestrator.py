from contextlib import suppress
from typing import Any

from app.automation.celery_app import celery
from app.automation.compensation import get_comp
from app.automation.metrics import runs_failed, runs_retried, runs_started, runs_success
from app.automation.registry import get_dag, get_skill, register_dag
from app.automation.state import set_status
from app.core.config import get_settings


async def run_dag(run_id: str, steps: list[str], context: dict[str, Any]) -> None:
    await set_status(run_id, "running", {"steps": steps})
    executed: list[str] = []
    try:
        # Optional research hook (no-op unless enabled)
        with suppress(Exception):
            s = get_settings()
            if getattr(s, "RESEARCH_ENABLED", False) and context.get("_blocker"):
                # import locally to avoid hard dep at import-time
                from tools.web_research import plan_queries

                _ = plan_queries(str(context["_blocker"]))
        for step in steps:
            fn = get_skill(step)
            context = await fn(context)
            executed.append(step)
            await set_status(run_id, "running", {"executed": executed})
        await set_status(run_id, "succeeded", {"executed": executed, "result": context})
    except Exception as e:  # pragma: no cover - simplest failure path
        await set_status(run_id, "failed", {"executed": executed, "error": str(e)})


# Register default DAGs at import so both API and worker see them
register_dag("lead.intake", ["lead.create_record", "lead.schedule_followup"])
register_dag("finance.pay_bill", ["finance.ocr_and_categorize", "finance.schedule_payment"])
register_dag("agent.prototype", ["prototype.enqueue_build"])
register_dag("ideation.generate", ["ideation.generate"])
register_dag("relationship.openers", ["relationship.generate_openers"])
register_dag(
    "business.marketing_launch",
    ["business.prepare_campaign", "business.launch_campaign", "business.collect_metrics"],
)
register_dag(
    "business.sales_outreach",
    ["business.prepare_outreach", "business.send_outreach"],
)
register_dag("business.ops_brief", ["business.ops_daily_briefing"])
register_dag(
    "business.simulate_cycle",
    [
        "ideation.generate",
        "business.prepare_campaign",
        "business.launch_campaign",
        "business.collect_metrics",
        "business.prepare_outreach",
        "business.send_outreach",
        "business.ops_daily_briefing",
    ],
)
register_dag(
    "documents.ingest_scan",
    [
        "documents.ocr_scan",
        "documents.classify",
        "documents.layout_analyze",
        "documents.extract_text",
    ],
)
register_dag(
    "finance.receipt_pipeline",
    [
        "finance.receipt_ocr",
        "finance.parse_amount",
        "finance.categorize",
        "finance.sync_accounting",
    ],
)
register_dag(
    "health.wellness_daily",
    [
        "health.collect_biometrics",
        "health.detect_anomaly",
        "health.trend_analyze",
    ],
)
register_dag(
    "nutrition.plan",
    [
        "nutrition.analyze",
        "nutrition.plan_meals",
    ],
)
register_dag(
    "home.evening_scene",
    [
        "home.presence_detect",
        "home.scene_evening",
        "home.energy_optimize",
    ],
)
register_dag(
    "transport.commute",
    [
        "transport.plan_route",
        "transport.optimize_cost",
    ],
)
register_dag(
    "learning.upskill",
    [
        "learning.assess_skills",
        "learning.plan_path",
        "learning.schedule",
    ],
)


@celery.task(name="automation.run_dag", bind=True, acks_late=True, max_retries=2)
def run_dag_task(self, run_id: str, intent: str, context: dict[str, Any]):
    import asyncio

    async def _run():
        runs_started.labels(intent).inc()
        steps: list[str] = get_dag(intent)
        await set_status(run_id, "running", {"steps": steps})
        executed: list[str] = []
        try:
            for step in steps:
                fn = get_skill(step)
                context_out = await fn(context)
                context.update(context_out)
                executed.append(step)
                await set_status(run_id, "running", {"executed": executed})
            await set_status(run_id, "succeeded", {"executed": executed, "result": context})
            runs_success.labels(intent).inc()
        except Exception as e:  # pragma: no cover - retry path
            if self.request.retries < self.max_retries:
                runs_retried.labels(intent).inc()
                await set_status(run_id, "retrying", {"error": str(e), "executed": executed})
                raise self.retry(exc=e, countdown=2 * (self.request.retries + 1)) from None
            await set_status(run_id, "failed", {"error": str(e), "executed": executed})
            runs_failed.labels(intent).inc()
        # Compensation pass (best-effort)
        for step in reversed(executed):
            comp = get_comp(step)
            if comp:
                with suppress(Exception):
                    comp(context)

    asyncio.run(_run())
