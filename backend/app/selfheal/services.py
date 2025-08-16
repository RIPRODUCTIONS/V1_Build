from __future__ import annotations

import asyncio
import contextlib
import json
import os
import urllib.request
from collections.abc import Collection, Iterable
from datetime import datetime, timezone

from app.core.config import get_settings

from .models import BuildResult, HealingResult, SystemHealth


class HealthMonitor:
    async def check_all_components(self) -> list[SystemHealth]:
        now = datetime.now(timezone.utc)
        results: list[SystemHealth] = []
        # API placeholder metrics
        results.append(
            SystemHealth(
                component="api",
                health_score=0.95,
                issues=[],
                performance_metrics={"p95_latency_ms": 42.0},
                last_check=now,
            )
        )
        # Database probe
        db_issues: list[str] = []
        db_score = 1.0
        try:
            from app.db import engine
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - depends on runtime env
            db_issues.append(f"db_error:{type(exc).__name__}")
            db_score = 0.0
        results.append(
            SystemHealth(
                component="db",
                health_score=db_score,
                issues=db_issues,
                performance_metrics={},
                last_check=now,
            )
        )
        # Redis probe (optional)
        redis_url = os.getenv("REDIS_URL")
        redis_issues: list[str] = []
        redis_score = 1.0
        if redis_url:
            try:
                import redis

                client = redis.from_url(redis_url, socket_connect_timeout=0.2)
                pong = client.ping()
                if not pong:
                    redis_score = 0.0
                    redis_issues.append("no_pong")
            except Exception as exc:  # pragma: no cover - depends on runtime env
                redis_score = 0.0
                redis_issues.append(f"redis_error:{type(exc).__name__}")
        results.append(
            SystemHealth(
                component="redis",
                health_score=redis_score,
                issues=redis_issues,
                performance_metrics={},
                last_check=now,
            )
        )
        # Worker placeholder
        results.append(
            SystemHealth(
                component="worker",
                health_score=0.88,
                issues=["sporadic queue spikes"],
                performance_metrics={"tasks_pending": 3.0},
                last_check=now,
            )
        )
        return results


class CodeGenerator:
    async def generate_component_code(self, requirements: dict) -> str:
        # Placeholder for AI codegen output
        return "# generated component code based on requirements\nclass Generated: ...\n"


class DeploymentEngine:
    async def deploy(self, component_code: str) -> bool:
        # Replace with real deployment pipeline (blue/green/canary)
        await asyncio.sleep(0.05)
        return True


class LearningEngine:
    async def learn_from_healing_attempts(self, issues: Iterable[SystemHealth]) -> None:
        # Persist telemetry and outcomes for future optimization
        _ = list(issues)


class ErrorAnalyzer:
    async def generate_healing_strategies(self, issue: SystemHealth) -> list[str]:
        # Return ordered strategies
        return ["restart-component", "clear-cache", "roll-back", "rebuild"]


class PerformanceOptimizer:
    async def test_optimization_safely(self, optimization: dict) -> dict:
        return {"improves_performance": True, "delta": {"cpu": -0.1}}


class SelfHealingCore:
    def __init__(self) -> None:
        self.health_monitor = HealthMonitor()
        self.code_generator = CodeGenerator()
        self.deployment_engine = DeploymentEngine()
        self.learning_engine = LearningEngine()
        self.error_analyzer = ErrorAnalyzer()
        self.performance_optimizer = PerformanceOptimizer()

    async def attempt_self_healing(self, health_issue: SystemHealth) -> HealingResult:
        strategies = await self.error_analyzer.generate_healing_strategies(health_issue)
        attempts = 0
        for strategy in strategies:
            attempts += 1
            try:
                # Placeholder: pretend first strategy succeeds for demo
                _record_heal_metric(health_issue.component, strategy, True)
                return HealingResult(success=True, message="healed", strategy_applied=strategy, attempts=attempts)
            except Exception:  # pragma: no cover - placeholder
                _record_heal_metric(health_issue.component, strategy, False)
                continue
        return HealingResult(success=False, message="All healing strategies failed", attempts=attempts)

    async def self_build_replacement(self, failed_component: SystemHealth) -> BuildResult:
        requirements = {"component_type": failed_component.component, "constraints": failed_component.performance_metrics}
        code = await self.code_generator.generate_component_code(requirements)
        # Placeholder test result
        improvements = {"cpu": 0.12}
        deployed = await self.deployment_engine.deploy(code)
        if deployed:
            return BuildResult(success=True, component=code, performance_improvements=improvements)
        return BuildResult(success=False, message="Deployment failed")

    async def continuous_health_monitoring(self, stop_event: asyncio.Event) -> None:
        """Continuously check components and try to heal.

        Runs until `stop_event` is set. Sleeps between cycles to avoid churn.
        """
        sleep_seconds = 30
        while not stop_event.is_set():
            try:
                status = await self.health_monitor.check_all_components()
                critical = [h for h in status if h.health_score < 0.7]
                for issue in critical:
                    result = await self.attempt_self_healing(issue)
                    if not result.success:
                        await self.self_build_replacement(issue)
                await self.learning_engine.learn_from_healing_attempts(critical)
                # Alert when issues detected
                try:
                    if critical:
                        s = get_settings()
                        payload = {
                            "kind": "self_heal_alert",
                            "issues": [
                                {"component": h.component, "score": h.health_score, "issues": h.issues}
                                for h in critical
                            ],
                        }
                        # Generic webhook
                        if s.alert_webhook_url:
                            req = urllib.request.Request(s.alert_webhook_url, method="POST")
                            req.add_header("Content-Type", "application/json")
                            urllib.request.urlopen(req, json.dumps(payload).encode(), timeout=5).read()
                        # Slack webhook
                        if s.slack_webhook_url:
                            issues_list: Collection[dict] = payload.get("issues", [])  # type: ignore[assignment]
                            text = "Self-heal issues: " + ", ".join(f"{i['component']}({i['score']})" for i in issues_list) or "none"
                            req = urllib.request.Request(s.slack_webhook_url, method="POST")
                            req.add_header("Content-Type", "application/json")
                            urllib.request.urlopen(req, json.dumps({"text": text}).encode(), timeout=5).read()
                        # Email (best-effort, plain SMTP)
                        if s.email_smtp_host and s.email_from and s.email_to and s.email_username and s.email_password:
                            import smtplib
                            from email.message import EmailMessage
                            msg = EmailMessage()
                            msg["Subject"] = "Self-heal alert"
                            msg["From"] = s.email_from
                            msg["To"] = s.email_to
                            msg.set_content(json.dumps(payload))
                            with smtplib.SMTP(s.email_smtp_host, int(s.email_smtp_port or 587), timeout=5) as smtp:
                                smtp.starttls()
                                smtp.login(s.email_username, s.email_password)
                                smtp.send_message(msg)
                except Exception:
                    pass
            except Exception:
                # Best-effort: keep loop alive
                pass
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=sleep_seconds)
            except TimeoutError:
                continue


# Optional Prometheus counters (best-effort)
try:  # pragma: no cover - metrics optional in tests
    from prometheus_client import Counter

    SELF_HEAL_ATTEMPTS = Counter(
        "selfheal_attempts_total",
        "Number of self-heal strategy applications",
        labelnames=("component", "strategy", "success"),
    )
except Exception:  # pragma: no cover
    SELF_HEAL_ATTEMPTS = None  # type: ignore


def _record_heal_metric(component: str, strategy: str, success: bool) -> None:
    if SELF_HEAL_ATTEMPTS is None:
        return
    with contextlib.suppress(Exception):
        SELF_HEAL_ATTEMPTS.labels(component=component, strategy=strategy, success=str(success)).inc()


