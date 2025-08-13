from __future__ import annotations

import json
from typing import Any, Dict, List
from app.db import SessionLocal
from app.models import AutomationTemplate


class AutomationTemplateLibrary:
    """In-memory template library scaffold. Replace with DB-backed loading later."""

    def __init__(self) -> None:
        self.templates: dict[str, dict[str, Any]] = {}
        self.load_templates()

    def load_templates(self) -> None:
        # Seed a few initial templates; expand to 15 incrementally
        self.templates = {
            "contact_form_lead_generator": {
                "id": "contact_form_lead_generator",
                "name": "Contact Form Lead Generator",
                "category": "lead_generation",
                "difficulty": "intermediate",
                "estimated_time_minutes": 4,
                "price_per_run_usd": 1.0,
                "description": "Find and submit contact forms to generate leads.",
                "required_parameters": [
                    {"name": "target_websites", "type": "list"},
                    {"name": "contact_message_template",
                     "type": "text"},
                    {"name": "sender_information", "type": "object"},
                ],
                "optional_parameters": [
                    {"name": "industry_filter", "type": "list"},
                    {"name": "company_size_filter", "type": "string"},
                    {"name": "follow_up_enabled", "type": "boolean", "default": False},
                ],
                "example_outputs": {"submitted": 10, "failed": 2},
            },
            "ecommerce_price_monitor": {
                "id": "ecommerce_price_monitor",
                "name": "E-commerce Price Monitor",
                "category": "ecommerce",
                "difficulty": "beginner",
                "estimated_time_minutes": 2,
                "price_per_run_usd": 1.5,
                "description": "Monitor product prices and availability.",
                "required_parameters": [
                    {"name": "product_urls", "type": "list"},
                    {"name": "monitoring_frequency", "type": "string"},
                ],
                "optional_parameters": [
                    {"name": "price_change_threshold", "type": "number", "default": 5.0},
                    {"name": "notification_email", "type": "email"},
                ],
                "example_outputs": {"alerts": 3},
            },
        }
        # Add revenue-focused templates
        self.templates.update({
            "linkedin_lead_extractor": {
                "id": "linkedin_lead_extractor",
                "name": "LinkedIn Lead Extractor",
                "category": "lead_generation",
                "estimated_time_minutes": 5,
                "price_per_run_usd": 2.0,
                "description": "Extract contact details from LinkedIn profiles for sales prospecting",
                "required_parameters": [{"name": "profile_urls", "type": "list"}],
                "optional_parameters": [],
            },
            "ecommerce_price_spy": {
                "id": "ecommerce_price_spy",
                "name": "E-commerce Price Spy",
                "category": "competitive_intelligence",
                "estimated_time_minutes": 2,
                "price_per_run_usd": 1.5,
                "description": "Monitor competitor prices and stock levels automatically",
                "required_parameters": [{"name": "product_urls", "type": "list"}],
                "optional_parameters": [],
            },
            "social_media_lead_harvester": {
                "id": "social_media_lead_harvester",
                "name": "Social Media Lead Harvester",
                "category": "lead_generation",
                "estimated_time_minutes": 8,
                "price_per_run_usd": 3.0,
                "description": "Find potential customers from social media posts and comments",
                "required_parameters": [{"name": "queries", "type": "list"}],
                "optional_parameters": [],
            },
            "job_board_auto_applier": {
                "id": "job_board_auto_applier",
                "name": "Job Board Auto-Applier",
                "category": "job_search",
                "estimated_time_minutes": 1,
                "price_per_run_usd": 0.5,
                "description": "Apply to multiple jobs automatically with personalized applications",
                "required_parameters": [{"name": "job_queries", "type": "list"}],
                "optional_parameters": [],
            },
            "review_reputation_monitor": {
                "id": "review_reputation_monitor",
                "name": "Review Reputation Monitor",
                "category": "reputation_management",
                "estimated_time_minutes": 3,
                "price_per_run_usd": 1.0,
                "description": "Monitor online reviews and mentions across platforms",
                "required_parameters": [{"name": "brand_terms", "type": "list"}],
                "optional_parameters": [],
            },
            # Personal automation templates (non-billing)
            "personal_email_manager": {
                "id": "personal_email_manager",
                "name": "Personal Email Manager",
                "category": "productivity",
                "estimated_time_minutes": 2,
                "description": "Automatically sort, respond to, and manage your personal emails",
                "required_parameters": [{"name": "labels", "type": "list", "optional": True}],
                "optional_parameters": [{"name": "auto_reply_templates", "type": "object", "optional": True}],
            },
            "personal_finance_tracker": {
                "id": "personal_finance_tracker",
                "name": "Personal Finance Tracker",
                "category": "finance",
                "estimated_time_minutes": 3,
                "description": "Track expenses, monitor accounts, and manage your personal finances",
                "required_parameters": [{"name": "accounts", "type": "list", "optional": True}],
                "optional_parameters": [{"name": "budgets", "type": "object", "optional": True}],
            },
            "social_media_manager": {
                "id": "social_media_manager",
                "name": "Personal Social Media Manager",
                "category": "social",
                "estimated_time_minutes": 2,
                "description": "Manage your social media presence and engagement",
                "required_parameters": [{"name": "platforms", "type": "list"}],
                "optional_parameters": [{"name": "schedule", "type": "list", "optional": True}],
            },
            "research_assistant": {
                "id": "research_assistant",
                "name": "Personal Research Assistant",
                "category": "research",
                "estimated_time_minutes": 5,
                "description": "Research topics, gather information, and create summaries for you",
                "required_parameters": [{"name": "topics", "type": "list"}],
                "optional_parameters": [{"name": "depth", "type": "string", "default": "thorough"}],
            },
            "shopping_assistant": {
                "id": "shopping_assistant",
                "name": "Personal Shopping Assistant",
                "category": "shopping",
                "estimated_time_minutes": 3,
                "description": "Find best deals, track prices, and manage your purchases",
                "required_parameters": [{"name": "wishlist", "type": "list", "optional": True}],
                "optional_parameters": [{"name": "retailers", "type": "list", "optional": True}],
            },
        })

    async def get_template(self, template_id: str) -> Dict[str, Any]:
        t = self.templates.get(template_id)
        if not t:
            raise KeyError(template_id)
        return t

    async def list_templates_by_category(self, category: str | None = None) -> List[Dict[str, Any]]:
        # Prefer DB-backed templates; fallback to in-memory if none
        db = SessionLocal()
        try:
            q = db.query(AutomationTemplate)
            if category:
                q = q.filter(AutomationTemplate.category == category)
            rows = q.order_by(AutomationTemplate.name.asc()).all()
            if rows:
                res: list[dict[str, Any]] = []
                for r in rows:
                    res.append(
                        {
                            "id": r.id,
                            "name": r.name,
                            "description": r.description,
                            "category": r.category,
                            "difficulty": r.difficulty,
                            "estimated_time_minutes": r.estimated_time_minutes,
                            "price_per_run_usd": r.price_per_run_usd,
                        }
                    )
                return res
        finally:
            db.close()
        items = list(self.templates.values())
        if category:
            items = [t for t in items if t.get("category") == category]
        return items

    async def categories(self) -> List[str]:
        db = SessionLocal()
        try:
            rows = db.query(AutomationTemplate.category).distinct().all()
            cats = sorted({c[0] for c in rows if c and c[0]})
            if cats:
                return cats
        finally:
            db.close()
        return sorted({t.get("category", "misc") for t in self.templates.values()})


