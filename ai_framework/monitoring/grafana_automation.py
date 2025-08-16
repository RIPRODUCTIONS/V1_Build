from __future__ import annotations

import base64
import os
from typing import Any

import requests


class GrafanaAutomation:
    """Automated Grafana dashboard setup for AI Framework monitoring."""

    # Constants to replace magic numbers
    PANEL_HEIGHT = 6
    PANEL_WIDTH_SMALL = 6
    PANEL_WIDTH_MEDIUM = 8
    PANEL_WIDTH_LARGE = 12
    PANEL_WIDTH_XLARGE = 24
    GRID_SPACING = 8
    REQUEST_TIMEOUT = 15

    def __init__(self, grafana_url: str = "http://localhost:3000") -> None:
        self.grafana_url = grafana_url.rstrip("/")
        self.admin_user = os.getenv("GRAFANA_ADMIN_USER", "admin")
        self.admin_password = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
        self.api_token = os.getenv("GRAFANA_API_TOKEN")

        if self.api_token:
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
        else:
            credentials = base64.b64encode(f"{self.admin_user}:{self.admin_password}".encode()).decode()
            self.headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            }

    def setup_complete_monitoring(self) -> None:
        self.create_system_overview_dashboard()
        self.create_department_performance_dashboard()

    def _post_dashboard(self, dashboard: dict[str, Any]) -> None:
        payload = {"dashboard": dashboard, "overwrite": True}
        resp = requests.post(f"{self.grafana_url}/api/dashboards/db", headers=self.headers, json=payload, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()

    def create_system_overview_dashboard(self) -> None:
        dashboard = {
            "id": None,
            "title": "AI Framework - System Overview",
            "tags": ["ai-framework", "production", "overview"],
            "timezone": "browser",
            "refresh": "30s",
            "time": {"from": "now-1h", "to": "now"},
            "panels": [
                {
                    "id": 1,
                    "title": "System Health Status",
                    "type": "stat",
                    "gridPos": {"h": self.PANEL_HEIGHT, "w": self.PANEL_WIDTH_SMALL, "x": 0, "y": 0},
                    "targets": [{"expr": "ai_framework_services_healthy", "refId": "A"}],
                },
                {
                    "id": 2,
                    "title": "CPU / Memory / Disk",
                    "type": "graph",
                    "gridPos": {"h": self.PANEL_HEIGHT, "w": self.PANEL_WIDTH_LARGE, "x": 6, "y": 0},
                    "targets": [
                        {"expr": "ai_framework_cpu_percent", "refId": "A"},
                        {"expr": "ai_framework_memory_percent", "refId": "B"},
                        {"expr": "ai_framework_disk_percent", "refId": "C"},
                    ],
                },
                {
                    "id": 3,
                    "title": "Queue Depths",
                    "type": "graph",
                    "gridPos": {"h": self.PANEL_HEIGHT, "w": self.PANEL_WIDTH_XLARGE, "x": 0, "y": 6},
                    "targets": [{"expr": "ai_framework_queue_depth", "legendFormat": "{{department}}", "refId": "A"}],
                },
            ],
        }
        self._post_dashboard(dashboard)

    def create_department_performance_dashboard(self) -> None:
        departments = [
            "finance",
            "sales",
            "marketing",
            "research",
            "operations",
            "hr",
            "legal",
            "executive",
        ]
        panels: list[dict[str, Any]] = []
        x = y = 0
        for i, dept in enumerate(departments, start=1):
            panels.append(
                {
                    "id": i,
                    "title": f"{dept.title()} Success Rate",
                    "type": "stat",
                    "gridPos": {"h": self.PANEL_HEIGHT, "w": self.PANEL_WIDTH_MEDIUM, "x": x, "y": y},
                    "targets": [
                        {
                            "expr": f"ai_framework_department_success_rate{{department=\"{dept}\"}}",
                            "refId": "A",
                        }
                    ],
                }
            )
            x += self.GRID_SPACING
            if x >= self.PANEL_WIDTH_XLARGE:
                x = 0
                y += self.PANEL_HEIGHT
        dashboard = {
            "id": None,
            "title": "AI Framework - Department Performance",
            "tags": ["ai-framework", "departments"],
            "timezone": "browser",
            "refresh": "1m",
            "panels": panels,
        }
        self._post_dashboard(dashboard)



