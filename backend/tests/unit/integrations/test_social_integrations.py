import json
import types
from urllib.error import URLError

import pytest

import app.integrations.social as social


class _Cfg:
    def __init__(self, **kwargs):
        # Defaults disabled
        self.twitter_enabled = kwargs.get("twitter_enabled", False)
        self.twitter_bearer_token = kwargs.get("twitter_bearer_token")
        self.twitter_user_token = kwargs.get("twitter_user_token")
        self.twitter_api_base = kwargs.get("twitter_api_base", "https://api.twitter.com")
        self.linkedin_enabled = kwargs.get("linkedin_enabled", False)
        self.linkedin_access_token = kwargs.get("linkedin_access_token")
        self.linkedin_member_urn = kwargs.get("linkedin_member_urn")
        self.post_real_enabled = kwargs.get("post_real_enabled", False)


def _ok_ctx(json_obj: dict):
    class _Resp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps(json_obj).encode("utf-8")
    return _Resp()


def test_twitter_disabled(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(twitter_enabled=False))
    integ = social.SocialIntegration()
    res = pytest.run(async_fn=integ._post_twitter, text="hi") if hasattr(pytest, 'run') else None
    # Fall back to async run
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_twitter("hi"))
    assert res["status"] == "disabled"


def test_twitter_dry_run_ok(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(twitter_enabled=True, twitter_bearer_token="t", post_real_enabled=False))
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_twitter("hello"))
    assert res["status"] == "ok" and res["id"] == "tweet_queued"


def test_twitter_post_success(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(twitter_enabled=True, twitter_bearer_token="t", post_real_enabled=True))
    # Patch urlopen to return OK JSON
    monkeypatch.setattr(social._req, "urlopen", lambda req, timeout=10: _ok_ctx({"id": "tw1"}))
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_twitter("hello"))
    assert res["status"] == "ok" and res["response"]["id"] == "tw1"


def test_twitter_post_url_error(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(twitter_enabled=True, twitter_bearer_token="t", post_real_enabled=True))
    def _boom(req, timeout=10):
        raise URLError("down")
    monkeypatch.setattr(social._req, "urlopen", _boom)
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_twitter("hello"))
    assert res["status"] == "error" and "detail" in res


def test_linkedin_disabled(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(linkedin_enabled=False))
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_linkedin("hi"))
    assert res["status"] == "disabled"


def test_linkedin_dry_run_ok(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(linkedin_enabled=True, linkedin_access_token="x", linkedin_member_urn="urn:li:person:123", post_real_enabled=False))
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_linkedin("hello"))
    assert res["status"] == "ok" and res["id"] == "linkedin_queued"


def test_linkedin_post_success(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(linkedin_enabled=True, linkedin_access_token="x", linkedin_member_urn="urn:li:person:123", post_real_enabled=True))
    monkeypatch.setattr(social._req, "urlopen", lambda req, timeout=10: _ok_ctx({"result": "ok"}))
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_linkedin("hello"))
    assert res["status"] == "ok"


def test_linkedin_post_url_error(monkeypatch):
    monkeypatch.setattr(social, "get_personal_config", lambda: _Cfg(linkedin_enabled=True, linkedin_access_token="x", linkedin_member_urn="urn:li:person:123", post_real_enabled=True))
    def _boom(req, timeout=10):
        raise URLError("no network")
    monkeypatch.setattr(social._req, "urlopen", _boom)
    integ = social.SocialIntegration()
    import asyncio
    res = asyncio.get_event_loop().run_until_complete(integ._post_linkedin("hello"))
    assert res["status"] == "error"


