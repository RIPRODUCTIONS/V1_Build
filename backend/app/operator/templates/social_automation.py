from __future__ import annotations

from typing import Any, Dict, List
from app.integrations.social import SocialIntegration


class PersonalSocialMediaManager:
    template_config = {
        "id": "social_media_manager",
        "name": "Personal Social Media Manager",
        "category": "social",
        "description": "Draft and schedule posts; future: real posting via integrations",
    }

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        text: str = parameters.get("text") or "Hello world"
        platforms: List[str] = parameters.get("platforms") or ["twitter", "linkedin"]
        post_now: bool = bool(parameters.get("post_now", False))
        user_id: int | None = None
        try:
            uid = parameters.get("user_id")
            user_id = int(uid) if uid is not None else None
        except Exception:
            user_id = None

        if not post_now:
            drafts = [{"platform": p, "draft": text} for p in platforms]
            return {"success": True, "posted": False, "drafts": drafts}

        integ = SocialIntegration()
        results = await integ.post(text, platforms, user_id=user_id)
        return {"success": True, "posted": True, "results": results}


