from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from app.core.config import get_settings
from prometheus_client import Counter

from .base import IntegrationBase


@dataclass(slots=True)
class GoogleMapsIntegration(IntegrationBase):
    name: str = "google_maps"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.metric_requests = Counter(
            "google_maps_requests_total",
            "Total Google Maps requests",
            labelnames=("endpoint", "status"),
        )
        self.metric_errors = Counter(
            "google_maps_errors_total",
            "Total Google Maps errors",
            labelnames=("endpoint", "code"),
        )

    async def discover(self, user_id: str) -> bool:
        return bool(self.settings.GOOGLE_MAPS_API_KEY)

    def _key(self) -> str:
        if not self.settings.GOOGLE_MAPS_API_KEY:
            raise RuntimeError("GOOGLE_MAPS_API_KEY not configured")
        return self.settings.GOOGLE_MAPS_API_KEY

    async def geocode(self, address: str) -> dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": self._key()}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            self.metric_requests.labels("geocode", str(r.status_code)).inc()
            if r.status_code >= 400:
                self.metric_errors.labels("geocode", str(r.status_code)).inc()
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            return {"status": "ok", "data": r.json()}

    async def directions(self, origin: str, destination: str, mode: str = "driving") -> dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self._key(),
        }
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, params=params)
            self.metric_requests.labels("directions", str(r.status_code)).inc()
            if r.status_code >= 400:
                self.metric_errors.labels("directions", str(r.status_code)).inc()
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            return {"status": "ok", "data": r.json()}

    async def distance_matrix(self, origins: list[str], destinations: list[str], mode: str = "driving") -> dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "key": self._key(),
        }
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, params=params)
            self.metric_requests.labels("distance_matrix", str(r.status_code)).inc()
            if r.status_code >= 400:
                self.metric_errors.labels("distance_matrix", str(r.status_code)).inc()
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            return {"status": "ok", "data": r.json()}

    async def places_search(self, query: str, location: str | None = None, radius: int | None = None) -> dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params: dict[str, Any] = {"query": query, "key": self._key()}
        if location:
            params["location"] = location
        if radius:
            params["radius"] = radius
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, params=params)
            self.metric_requests.labels("places", str(r.status_code)).inc()
            if r.status_code >= 400:
                self.metric_errors.labels("places", str(r.status_code)).inc()
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            return {"status": "ok", "data": r.json()}


