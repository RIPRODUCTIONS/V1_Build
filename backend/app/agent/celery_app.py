from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("builder", broker=REDIS_URL, backend=REDIS_URL, include=[
    "app.agent.tasks",
    "app.integrations.tasks",
    "app.automations.tasks",
    "app.tasks.web_automation_tasks",
    "app.tasks.personal_automation_tasks",
    "app.tasks.investigation_tasks",
    "app.monitoring.celery_metrics",
])

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_routes={
        "app.agent.tasks.run_pipeline_task": {"queue": "agent"},
        "app.agent.tasks.create_followup_task": {"queue": "default"},
        "app.integrations.tasks.*": {"queue": "integrations"},
        "app.automations.tasks.*": {"queue": "automations"},
        # Route Playwright/web browsing tasks to dedicated webexec queue
        "automation.execute_web_task": {"queue": "webexec"},
        "personal.research.execute": {"queue": "webexec"},
        "personal.shopping.execute": {"queue": "webexec"},
        # Generic matcher for future webexec.* tasks
        "webexec.*": {"queue": "webexec"},
        "personal.social.execute": {"queue": "automations"},
        "personal.email.execute": {"queue": "automations"},
        "personal.finance.execute": {"queue": "automations"},
        "investigation.osint.run": {"queue": "automations"},
        "investigation.finance.run": {"queue": "automations"},
            "investigation.forensics.timeline.run": {"queue": "automations"},
            "investigation.malware.dynamic.run": {"queue": "automations"},
            "investigation.threat.apt_attribution.run": {"queue": "automations"},
            "investigation.supplychain.sca.run": {"queue": "automations"},
            "investigation.autopilot.run": {"queue": "automations"},
        "coverage.expand": {"queue": "automations"},
    },
    beat_schedule={
        # Nightly housekeeping at 03:00 UTC: cleanup artifacts older than 30 days
        "cleanup_old_runs": {
            "task": "maintenance.cleanup_runs",
            "schedule": 24 * 60 * 60,  # daily
            "args": [30],
        },
        # Integration syncs: every 15 minutes
        "integrations_sync_all_users": {
            "task": "app.integrations.tasks.discover_new_integrations",
            "schedule": 15 * 60,
            "args": ["u1"],  # TODO: iterate real user ids
        },
        # Per-user full sync every 10 minutes (user_id "1")
        "integrations_sync_user_1": {
            "task": "app.integrations.tasks.sync_user_all",
            "schedule": 10 * 60,
            "args": ["1"],
        },
        # Token refresh every 30 minutes
        "integrations_refresh_tokens": {
            "task": "app.integrations.tasks.refresh_expiring_tokens",
            "schedule": 30 * 60,
        },
            # Optional: Autopilot daily (disabled by default via ENV)
            # Enable by setting AUTOPILOT_SCHEDULE_ENABLED=true
            **(
                {"investigations_autopilot_daily": {
                    "task": "investigation.autopilot.run",
                    "schedule": 24 * 60 * 60,
                    "args": [{"subject": {"name": "Jane Doe"}}],
                }} if os.getenv("AUTOPILOT_SCHEDULE_ENABLED", "false").lower() == "true" else {}
            ),
            # Optional: Coverage expansion hourly
            **(
                {"coverage_expand_hourly": {
                    "task": "coverage.expand",
                    "schedule": 60 * 60,
                    "args": [{"topics": [
                        "osint techniques", "digital forensics timeline", "apt tracking",
                        "insurance fraud signals", "crypto tumblers"
                    ]}],
                }} if os.getenv("COVERAGE_EXPAND_ENABLED", "false").lower() == "true" else {}
            ),
            **(
                {"assistant_self_build_scan_daily": {
                    "task": "app.agent.tasks.noop",  # use a lightweight task name; actual scan via app route runner
                    "schedule": 24 * 60 * 60,
                }} if os.getenv("SELF_BUILD_SCAN_ENABLED", "false").lower() == "true" else {}
            ),
            **(
                {"system_autonomy_tick": {
                    "task": "system.autonomy.tick",
                    "schedule": 10 * 60,
                }} if os.getenv("SYSTEM_AUTONOMY_ENABLED", "false").lower() == "true" else {}
            ),
            # Synthetic monitors (opt-in)
            **(
                {"monitor_synthetic_osint_hourly": {
                    "task": "monitor.synthetic.osint",
                    "schedule": 60 * 60,
                }} if os.getenv("SYNTHETIC_OSINT_ENABLED", "false").lower() == "true" else {}
            ),
            **(
                {"monitor_sse_watchdog": {
                    "task": "monitor.sse.watchdog",
                    "schedule": 60,
                }} if os.getenv("SSE_WATCHDOG_ENABLED", "false").lower() == "true" else {}
            ),
    },
)
