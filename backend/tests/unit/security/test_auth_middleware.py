import pytest
from fastapi import HTTPException
from app.middleware.auth import validate_api_key


class TestAPIKeyValidation:
    @pytest.mark.asyncio
    async def test_valid_key(self, monkeypatch):
        monkeypatch.setenv("SECURE_MODE", "true")
        monkeypatch.setenv("INTERNAL_API_KEY", "k")
        assert await validate_api_key("k") == "k"

    @pytest.mark.asyncio
    async def test_invalid_key(self, monkeypatch):
        monkeypatch.setenv("SECURE_MODE", "true")
        monkeypatch.setenv("INTERNAL_API_KEY", "k")
        with pytest.raises(HTTPException):
            await validate_api_key("bad")

    @pytest.mark.asyncio
    async def test_missing_key_header(self, monkeypatch):
        monkeypatch.setenv("SECURE_MODE", "true")
        monkeypatch.setenv("INTERNAL_API_KEY", "k")
        with pytest.raises(HTTPException):
            await validate_api_key(None)



