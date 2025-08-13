from __future__ import annotations


class PersonalConfig:
    """Personal account preferences (edit locally)."""

    PERSONAL_EMAIL = "your.email@gmail.com"
    EMAIL_CHECK_FREQUENCY_MIN = 30
    EMAIL_CATEGORIES = ["bills", "newsletters", "personal", "work", "actionable"]

    BANK_ACCOUNTS = [
        {"name": "Main Checking", "type": "checking", "import_method": "csv"},
        {"name": "Savings", "type": "savings", "import_method": "csv"},
        {"name": "Credit Card", "type": "credit", "import_method": "csv"},
    ]
    BUDGET_CATEGORIES = {
        "food": 800,
        "transport": 300,
        "utilities": 200,
        "entertainment": 400,
        "shopping": 500,
    }

    SOCIAL_ACCOUNTS = {
        "twitter": {"username": "@yourusername", "auto_post": True},
        "linkedin": {"profile": "your-linkedin", "auto_post": True},
    }
    OPTIMAL_POST_TIMES = ["09:00", "13:00", "17:00"]

    RESEARCH_INTERESTS = ["AI", "automation", "productivity", "technology"]
    RESEARCH_SOURCES = ["arxiv", "google_scholar", "news", "reddit"]

    DAILY_AUTOMATIONS = {
        "08:00": ["personal_email_manager", "calendar_briefing"],
        "12:00": ["social_media_check"],
        "18:00": ["finance_update"],
        "22:00": ["daily_summary"],
    }


