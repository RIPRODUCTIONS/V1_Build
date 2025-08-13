from __future__ import annotations

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List
import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.automations.actions import ActionExecutor
from app.automations.metrics import automation_rule_executions, automation_rule_latency
from app.automations.models import AutomationRule, RuleExecution


logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, db: Session):
        self.db = db
        self.action_executor = ActionExecutor()

    async def evaluate_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all DB rules against an incoming event dict.

        Event schema expected: {"type", "user_id", "ts", "payload": {...}}
        """
        user_id = str(event.get("user_id", ""))
        event_type = str(event.get("type", ""))
        logger.info("Evaluating event type=%s user=%s", event_type, user_id)

        rules: List[AutomationRule] = (
            self.db.query(AutomationRule)
            .filter(
                or_(AutomationRule.user_id == user_id, AutomationRule.user_id == "system"),
                AutomationRule.enabled.is_(True),
                (AutomationRule.event_pattern == event_type),
            )
            .all()
        )
        logger.info("Loaded %d rules for evaluation", len(rules))

        executions: List[Dict[str, Any]] = []
        for rule in rules:
            try:
                if self.check_conditions(rule.conditions or {}, event):
                    # Execute sequentially; extend later to parallel if needed
                    results: List[Dict[str, Any]] = []
                    for action in rule.actions or []:
                        with automation_rule_latency.labels(rule_name=rule.id).time():
                            res = await self.action_executor.execute(
                                action_type=action.get("type", ""),
                                params=action.get("params", {}),
                                context={
                                    "user_id": user_id,
                                    "event": event.get("payload", {}),
                                    "rule_id": rule.id,
                                },
                                db=self.db,
                            )
                        results.append(res)
                    self.log_execution(rule_id=rule.id, event_id=event.get("id") or "", status="success", result={"actions": results})
                    rule.execution_count = (rule.execution_count or 0) + 1
                    rule.last_executed = datetime.utcnow()
                    self.db.commit()
                    automation_rule_executions.labels(rule_name=rule.id, status="success").inc()
                    executions.append({"rule": rule.id, "status": "success", "results": results})
                else:
                    automation_rule_executions.labels(rule_name=rule.id, status="skipped").inc()
                    executions.append({"rule": rule.id, "status": "skipped", "reason": "conditions_not_met"})
            except Exception as e:
                self.log_execution(rule_id=rule.id, event_id=event.get("id") or "", status="failed", error=str(e))
                automation_rule_executions.labels(rule_name=rule.id, status="failed").inc()
                executions.append({"rule": rule.id, "status": "failed", "error": str(e)})

        return executions

    def check_conditions(self, conditions: Dict[str, Any], event: Dict[str, Any]) -> bool:
        if not conditions:
            return True
        if "any" in conditions:
            return any(self.evaluate_single_condition(c, event) for c in conditions.get("any", []))
        if "all" in conditions:
            return all(self.evaluate_single_condition(c, event) for c in conditions.get("all", []))
        return self.evaluate_single_condition(conditions, event)

    def evaluate_single_condition(self, condition: Dict[str, Any], event: Dict[str, Any]) -> bool:
        try:
            payload = event.get("payload", {})
            # Text contains
            if "title_contains" in condition:
                title = str(payload.get("title", "")).lower()
                search = str(condition["title_contains"]).lower()
                matched = search in title
                logger.info("Condition title_contains '%s' in '%s' => %s", search, title, matched)
                return matched
            if "attendee_includes" in condition:
                raw = payload.get("raw_data", {}) or {}
                attendees = [
                    (a.get("email") or "").lower()
                    for a in (raw.get("attendees", []) or [])
                    if isinstance(a, dict)
                ]
                target = str(condition["attendee_includes"]).lower()
                return target in attendees
            if "subject_contains" in condition:
                subject = str(payload.get("subject", "")).lower()
                return condition["subject_contains"].lower() in subject
            if "body_contains" in condition:
                body = str(payload.get("body", "")).lower()
                return condition["body_contains"].lower() in body
            # Booleans
            if "from_vip" in condition:
                return bool(payload.get("from_vip", False)) == bool(condition["from_vip"])
            # Time window
            if "time_range" in condition and payload.get("timestamp"):
                from datetime import time as dtime, datetime as dt

                ev_time = dt.fromisoformat(str(payload["timestamp"]).replace("Z", "+00:00")).time()
                start_s = condition["time_range"].get("start", "00:00")
                end_s = condition["time_range"].get("end", "23:59")
                h1, m1 = map(int, start_s.split(":"))
                h2, m2 = map(int, end_s.split(":"))
                return dtime(h1, m1) <= ev_time <= dtime(h2, m2)
            # Default permissive
            return True
        except Exception:
            return False

    def log_execution(self, rule_id: str, event_id: str, status: str, result: Dict[str, Any] | None = None, error: str | None = None) -> None:
        exec_row = RuleExecution(
            id=str(uuid.uuid4()),
            rule_id=rule_id,
            event_id=event_id,
            status=status,
            result=result,
            error=error,
            executed_at=datetime.utcnow(),
        )
        self.db.add(exec_row)
        self.db.commit()


