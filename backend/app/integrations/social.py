from __future__ import annotations

from typing import Any, Dict, List

from app.personal.personal_config import get_personal_config
from app.db import SessionLocal
import asyncio
import json
from urllib import request as _req
from urllib.error import HTTPError, URLError


class SocialIntegration:
    def __init__(self) -> None:
        self.cfg = get_personal_config()

    async def post(self, text: str, platforms: List[str], *, user_id: int | None = None) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for p in platforms:
            if p.lower() == "twitter":
                results[p] = await self._post_twitter(text)
            elif p.lower() == "linkedin":
                results[p] = await self._post_linkedin(text)
            else:
                results[p] = {"status": "unsupported"}
        return results

    async def _post_twitter(self, text: str, *, user_id: int | None = None) -> Dict[str, Any]:
        # Prefer stored token if available
        token_db: str | None = None
        try:
            from app.models import SocialAuth
            db = SessionLocal()
            try:
                q = db.query(SocialAuth).filter(SocialAuth.provider == "twitter")
                if user_id:
                    q = q.filter(SocialAuth.user_id == user_id)
                rec = q.order_by(SocialAuth.id.desc()).first()
                if rec and rec.access_token:
                    token_db = rec.access_token
            finally:
                db.close()
        except Exception:
            token_db = None

        if not (self.cfg.twitter_enabled and (token_db or self.cfg.twitter_bearer_token or self.cfg.twitter_user_token)):
            return {"status": "disabled"}
        if not self.cfg.post_real_enabled:
            return {"status": "ok", "id": "tweet_queued"}
        token = token_db or self.cfg.twitter_user_token or self.cfg.twitter_bearer_token
        api_base = (self.cfg.twitter_api_base or "https://api.twitter.com").rstrip("/")
        url = f"{api_base}/2/tweets"
        payload = json.dumps({"text": text}).encode("utf-8")

        def _do() -> Dict[str, Any]:
            req = _req.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", f"Bearer {token}")
            try:
                with _req.urlopen(req, timeout=10) as resp:  # nosec - controlled URL
                    data = json.loads(resp.read().decode("utf-8"))
                    return {"status": "ok", "response": data}
            except HTTPError as e:  # pragma: no cover - network
                try:
                    body = e.read().decode("utf-8")
                except Exception:
                    body = str(e)
                return {"status": "error", "code": e.code, "detail": body}
            except URLError as e:  # pragma: no cover - network
                return {"status": "error", "detail": str(e)}

        return await asyncio.to_thread(_do)

    async def _post_linkedin(self, text: str, *, user_id: int | None = None) -> Dict[str, Any]:
        # Prefer stored token if available
        token_db: str | None = None
        try:
            from app.models import SocialAuth
            db = SessionLocal()
            try:
                q = db.query(SocialAuth).filter(SocialAuth.provider == "linkedin")
                if user_id:
                    q = q.filter(SocialAuth.user_id == user_id)
                rec = q.order_by(SocialAuth.id.desc()).first()
                if rec and rec.access_token:
                    token_db = rec.access_token
            finally:
                db.close()
        except Exception:
            token_db = None

        if not (self.cfg.linkedin_enabled and (token_db or self.cfg.linkedin_access_token) and self.cfg.linkedin_member_urn):
            return {"status": "disabled"}
        if not self.cfg.post_real_enabled:
            return {"status": "ok", "id": "linkedin_queued"}
        url = "https://api.linkedin.com/v2/ugcPosts"
        payload_obj = {
            "author": self.cfg.linkedin_member_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        payload = json.dumps(payload_obj).encode("utf-8")

        def _do() -> Dict[str, Any]:
            req = _req.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Restli-Protocol-Version", "2.0.0")
            req.add_header("Authorization", f"Bearer {token_db or self.cfg.linkedin_access_token}")
            try:
                with _req.urlopen(req, timeout=10) as resp:  # nosec - external API
                    data = json.loads(resp.read().decode("utf-8") or "{}")
                    return {"status": "ok", "response": data}
            except HTTPError as e:  # pragma: no cover - network
                try:
                    body = e.read().decode("utf-8")
                except Exception:
                    body = str(e)
                return {"status": "error", "code": e.code, "detail": body}
            except URLError as e:  # pragma: no cover - network
                return {"status": "error", "detail": str(e)}

        return await asyncio.to_thread(_do)


