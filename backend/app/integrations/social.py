from __future__ import annotations

from typing import Any, Dict, List

from app.personal.personal_config import get_personal_config


class SocialIntegration:
    def __init__(self) -> None:
        self.cfg = get_personal_config()

    async def post(self, text: str, platforms: List[str]) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for p in platforms:
            if p.lower() == "twitter":
                results[p] = await self._post_twitter(text)
            elif p.lower() == "linkedin":
                results[p] = await self._post_linkedin(text)
            else:
                results[p] = {"status": "unsupported"}
        return results

    async def _post_twitter(self, text: str) -> Dict[str, Any]:
        if not (self.cfg.twitter_enabled and self.cfg.twitter_bearer_token):
            return {"status": "disabled"}
        # Placeholder: real call would use Twitter API v2/v1.1 as applicable
        return {"status": "ok", "id": "tweet_123"}

    async def _post_linkedin(self, text: str) -> Dict[str, Any]:
        if not (self.cfg.linkedin_enabled and self.cfg.linkedin_access_token):
            return {"status": "disabled"}
        # Placeholder: real call would use LinkedIn API
        return {"status": "ok", "id": "li_123"}


