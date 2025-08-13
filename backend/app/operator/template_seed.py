from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import AutomationTemplate


SEED_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "contact_form_lead_generator",
        "name": "Contact Form Lead Generator",
        "description": "Find and submit contact forms to generate leads.",
        "category": "lead_generation",
        "difficulty": "intermediate",
        "estimated_time_minutes": 4,
        "business_value_description": "Automate outreach and capture qualified leads.",
        "success_rate": 0.0,
        "usage_count": 0,
        "template_config": {"executor": "contact_form"},
        "required_parameters": [
            {"name": "target_websites", "type": "list"},
            {"name": "contact_message_template", "type": "text"},
            {"name": "sender_information", "type": "object"},
        ],
        "optional_parameters": [
            {"name": "industry_filter", "type": "list"},
            {"name": "company_size_filter", "type": "string"},
        ],
        "example_outputs": {"submitted": 10, "failed": 2},
    },
    {
        "id": "ecommerce_price_monitor",
        "name": "E-commerce Price Monitor",
        "description": "Monitor product prices and availability.",
        "category": "ecommerce",
        "difficulty": "beginner",
        "estimated_time_minutes": 2,
        "business_value_description": "Track competitors to optimize pricing.",
        "success_rate": 0.0,
        "usage_count": 0,
        "template_config": {"executor": "price_monitor"},
        "required_parameters": [
            {"name": "product_urls", "type": "list"},
            {"name": "monitoring_frequency", "type": "string"},
        ],
        "optional_parameters": [
            {"name": "price_change_threshold", "type": "number", "default": 5.0},
        ],
        "example_outputs": {"alerts": 3},
    },
    {"id": "linkedin_profile_extractor", "name": "LinkedIn Profile Data Extractor", "description": "Extract professional data from LinkedIn profiles.", "category": "lead_generation", "difficulty": "intermediate", "estimated_time_minutes": 3, "business_value_description": "Prospecting at scale.", "template_config": {"executor": "scrape"}, "required_parameters": [{"name": "profile_urls", "type": "list"}], "optional_parameters": [{"name": "export_format", "type": "string", "default": "csv"}]},
    {"id": "social_media_cross_poster", "name": "Social Media Cross-Posting", "description": "Post content across multiple platforms.", "category": "social_media", "difficulty": "intermediate", "estimated_time_minutes": 5, "business_value_description": "Consistent presence.", "template_config": {"executor": "social"}, "required_parameters": [{"name": "content", "type": "text"}, {"name": "platforms", "type": "list"}], "optional_parameters": [{"name": "hashtags", "type": "list"}]},
    {"id": "crm_data_entry_automation", "name": "CRM Data Entry Automation", "description": "Automate CRM data entry.", "category": "crm_automation", "difficulty": "advanced", "estimated_time_minutes": 6, "business_value_description": "Eliminate manual entry.", "template_config": {"executor": "crm"}, "required_parameters": [{"name": "crm_platform", "type": "string"}], "optional_parameters": [{"name": "duplicate_handling", "type": "string", "default": "skip"}]},
    {"id": "job_application_automation", "name": "Job Application Automation", "description": "Apply to jobs automatically.", "category": "content_creation", "difficulty": "intermediate", "estimated_time_minutes": 4, "business_value_description": "Save applicant time.", "template_config": {"executor": "forms"}, "required_parameters": [{"name": "job_urls", "type": "list"}], "optional_parameters": []},
    {"id": "review_rating_monitor", "name": "Review and Rating Monitor", "description": "Monitor reviews and ratings.", "category": "monitoring", "difficulty": "beginner", "estimated_time_minutes": 2, "business_value_description": "Reputation management.", "template_config": {"executor": "monitor"}, "required_parameters": [{"name": "listing_urls", "type": "list"}], "optional_parameters": [{"name": "threshold", "type": "number", "default": 1.0}]},
    {"id": "competitor_analysis", "name": "Competitor Analysis Automation", "description": "Analyze competitor content.", "category": "data_extraction", "difficulty": "intermediate", "estimated_time_minutes": 5, "business_value_description": "Insights.", "template_config": {"executor": "scrape"}, "required_parameters": [{"name": "competitor_sites", "type": "list"}], "optional_parameters": []},
    {"id": "email_list_building", "name": "Email List Building from Websites", "description": "Collect emails from sites.", "category": "lead_generation", "difficulty": "advanced", "estimated_time_minutes": 6, "business_value_description": "Lead capture.", "template_config": {"executor": "scrape"}, "required_parameters": [{"name": "target_sites", "type": "list"}], "optional_parameters": []},
    {"id": "event_registration_automation", "name": "Event Registration Automation", "description": "Register for events.", "category": "content_creation", "difficulty": "beginner", "estimated_time_minutes": 3, "business_value_description": "Time saver.", "template_config": {"executor": "forms"}, "required_parameters": [{"name": "event_urls", "type": "list"}], "optional_parameters": []},
    {"id": "survey_auto_completion", "name": "Survey and Form Auto-Completion", "description": "Auto-complete surveys.", "category": "content_creation", "difficulty": "intermediate", "estimated_time_minutes": 4, "business_value_description": "Scale responses.", "template_config": {"executor": "forms"}, "required_parameters": [{"name": "survey_urls", "type": "list"}], "optional_parameters": []},
    {"id": "website_change_monitor", "name": "Website Change Monitor", "description": "Monitor website changes.", "category": "monitoring", "difficulty": "beginner", "estimated_time_minutes": 2, "business_value_description": "Stay informed.", "template_config": {"executor": "monitor"}, "required_parameters": [{"name": "pages", "type": "list"}], "optional_parameters": []},
    {"id": "seo_data_collection", "name": "SEO Data Collection", "description": "Collect SEO signals.", "category": "data_extraction", "difficulty": "intermediate", "estimated_time_minutes": 3, "business_value_description": "Improve SEO.", "template_config": {"executor": "scrape"}, "required_parameters": [{"name": "keywords", "type": "list"}], "optional_parameters": []},
    {"id": "support_ticket_creation", "name": "Customer Support Ticket Creation", "description": "Create tickets across systems.", "category": "crm_automation", "difficulty": "intermediate", "estimated_time_minutes": 3, "business_value_description": "Faster support.", "template_config": {"executor": "crm"}, "required_parameters": [{"name": "source_emails", "type": "list"}], "optional_parameters": []},
    {"id": "inventory_level_checking", "name": "Inventory Level Checking", "description": "Check stock availability.", "category": "ecommerce", "difficulty": "beginner", "estimated_time_minutes": 2, "business_value_description": "Avoid stockouts.", "template_config": {"executor": "monitor"}, "required_parameters": [{"name": "product_urls", "type": "list"}], "optional_parameters": []},
]


def seed_templates(db: Session) -> int:
    created = 0
    for t in SEED_TEMPLATES:
        if db.get(AutomationTemplate, t["id"]):
            continue
        rec = AutomationTemplate(
            id=t["id"],
            name=t["name"],
            description=t.get("description"),
            category=t["category"],
            difficulty=t.get("difficulty"),
            estimated_time_minutes=t.get("estimated_time_minutes"),
            business_value_description=t.get("business_value_description"),
            success_rate=float(t.get("success_rate", 0.0)),
            usage_count=int(t.get("usage_count", 0)),
            template_config_json=json.dumps(t.get("template_config", {})),
            required_parameters_json=json.dumps(t.get("required_parameters", [])),
            optional_parameters_json=json.dumps(t.get("optional_parameters", [])),
            example_outputs_json=json.dumps(t.get("example_outputs", {})),
        )
        db.add(rec)
        created += 1
    if created:
        db.commit()
    return created


