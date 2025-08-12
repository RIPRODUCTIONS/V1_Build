from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AutomationPlan:
    """Plan for executing an automation."""

    run_id: str
    intent: str
    department: str
    correlation_id: Optional[str] = None
    steps: list[str] = None
    priority: str = "normal"
    estimated_duration: str = "5-15 minutes"
    dependencies: list[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class RuleBasedPlanner:
    """Rule-based planner for determining automation execution plans."""

    def __init__(self):
        # Department mapping rules
        self.department_rules = {
            "life": {
                "patterns": ["life.", "health.", "nutrition.", "home.", "transport.", "learning."],
                "capabilities": [
                    "personal_automation",
                    "daily_routines",
                    "wellness",
                    "productivity",
                ],
                "priority": "high",
                "estimated_duration": "2-10 minutes",
            },
            "finance": {
                "patterns": ["finance.", "investment.", "bills.", "budget.", "trading."],
                "capabilities": [
                    "financial_analysis",
                    "portfolio_management",
                    "bill_payment",
                    "budgeting",
                ],
                "priority": "high",
                "estimated_duration": "5-30 minutes",
            },
            "safety": {
                "patterns": ["security.", "safety.", "monitoring.", "alert."],
                "capabilities": ["security_scanning", "threat_detection", "compliance_checking"],
                "priority": "critical",
                "estimated_duration": "1-5 minutes",
            },
            "business": {
                "patterns": ["business.", "marketing.", "sales.", "ops.", "strategy."],
                "capabilities": [
                    "market_analysis",
                    "campaign_management",
                    "sales_automation",
                    "operations",
                ],
                "priority": "medium",
                "estimated_duration": "15-60 minutes",
            },
            "research": {
                "patterns": ["research.", "analysis.", "investigation.", "discovery."],
                "capabilities": ["data_analysis", "market_research", "trend_analysis", "insights"],
                "priority": "medium",
                "estimated_duration": "30-120 minutes",
            },
            "engineering": {
                "patterns": ["build.", "deploy.", "test.", "code.", "infra."],
                "capabilities": ["software_development", "deployment", "testing", "infrastructure"],
                "priority": "medium",
                "estimated_duration": "60-300 minutes",
            },
        }

        # Step templates for different automation types
        self.step_templates = {
            "life": {
                "health.wellness_daily": [
                    "check_health_metrics",
                    "generate_wellness_plan",
                    "schedule_activities",
                ],
                "nutrition.plan": [
                    "analyze_nutrition_needs",
                    "generate_meal_plan",
                    "create_shopping_list",
                ],
                "home.evening_scene": [
                    "check_home_status",
                    "optimize_environment",
                    "prepare_evening_routine",
                ],
                "transport.commute": [
                    "check_traffic_conditions",
                    "optimize_route",
                    "update_schedule",
                ],
                "learning.upskill": [
                    "assess_current_skills",
                    "identify_learning_gaps",
                    "create_study_plan",
                ],
            },
            "finance": {
                "finance.investments_daily": [
                    "check_portfolio_status",
                    "analyze_market_conditions",
                    "generate_recommendations",
                ],
                "finance.bills_monthly": [
                    "scan_for_bills",
                    "prioritize_payments",
                    "schedule_payments",
                ],
            },
            "safety": {
                "security.weekly_sweep": [
                    "scan_systems",
                    "check_vulnerabilities",
                    "generate_security_report",
                ]
            },
        }

    def infer_department(self, intent: str) -> str:
        """Infer department from automation intent."""
        if not intent or "." not in intent:
            return "general"

        intent_prefix = intent.split(".", 1)[0]

        for dept, rules in self.department_rules.items():
            for pattern in rules["patterns"]:
                if intent.startswith(pattern):
                    return dept

        # Fallback based on intent prefix
        if intent_prefix in ["health", "nutrition", "home", "transport", "learning"]:
            return "life"
        elif intent_prefix in ["investment", "bills", "budget", "trading"]:
            return "finance"
        elif intent_prefix in ["security", "safety", "monitoring"]:
            return "safety"
        elif intent_prefix in ["marketing", "sales", "ops", "strategy"]:
            return "business"
        elif intent_prefix in ["research", "analysis", "investigation"]:
            return "research"
        elif intent_prefix in ["build", "deploy", "test", "code", "infra"]:
            return "engineering"

        return "general"

    def get_execution_steps(self, intent: str, department: str) -> list[str]:
        """Get execution steps for an automation."""
        if department in self.step_templates and intent in self.step_templates[department]:
            return self.step_templates[department][intent].copy()

        # Generic steps based on department
        generic_steps = {
            "life": ["analyze_context", "generate_plan", "execute_automation", "record_results"],
            "finance": ["gather_data", "analyze_metrics", "make_decisions", "execute_actions"],
            "safety": ["assess_risk", "scan_systems", "generate_alerts", "log_actions"],
            "business": ["analyze_market", "plan_strategy", "execute_campaign", "measure_results"],
            "research": ["define_scope", "gather_information", "analyze_data", "generate_insights"],
            "engineering": ["plan_implementation", "write_code", "run_tests", "deploy_solution"],
        }

        return generic_steps.get(department, ["plan", "execute", "validate", "complete"]).copy()

    def get_priority(self, department: str, intent: str) -> str:
        """Get priority for an automation."""
        if department in self.department_rules:
            return self.department_rules[department]["priority"]

        # High priority for safety and critical operations
        if "security" in intent or "safety" in intent:
            return "critical"
        elif "finance" in intent or "health" in intent:
            return "high"
        else:
            return "normal"

    def get_estimated_duration(self, department: str, intent: str) -> str:
        """Get estimated duration for an automation."""
        if department in self.department_rules:
            return self.department_rules[department]["estimated_duration"]

        # Estimate based on intent complexity
        if "daily" in intent or "quick" in intent:
            return "2-5 minutes"
        elif "weekly" in intent or "analysis" in intent:
            return "10-30 minutes"
        elif "monthly" in intent or "report" in intent:
            return "30-60 minutes"
        elif "build" in intent or "deploy" in intent:
            return "60-300 minutes"
        else:
            return "5-15 minutes"

    def create_plan(
        self, run_id: str, intent: str, correlation_id: Optional[str] = None
    ) -> AutomationPlan:
        """Create a complete automation plan."""
        department = self.infer_department(intent)
        steps = self.get_execution_steps(intent, department)
        priority = self.get_priority(department, intent)
        estimated_duration = self.get_estimated_duration(department, intent)

        # Add department-specific metadata
        metadata = {
            "department_capabilities": self.department_rules.get(department, {}).get(
                "capabilities", []
            ),
            "intent_pattern": intent.split(".", 1)[0] if "." in intent else intent,
            "planning_timestamp": "now",
        }

        return AutomationPlan(
            run_id=run_id,
            intent=intent,
            department=department,
            correlation_id=correlation_id,
            steps=steps,
            priority=priority,
            estimated_duration=estimated_duration,
            metadata=metadata,
        )


# Global planner instance
planner = RuleBasedPlanner()
