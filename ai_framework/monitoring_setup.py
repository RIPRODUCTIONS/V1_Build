#!/usr/bin/env python3
"""Production Monitoring Setup (Grafana/Prometheus config helpers)."""

from __future__ import annotations

import json
from pathlib import Path


def setup_grafana_dashboard() -> Path:
    dashboard_config = {
        "dashboard": {
            "title": "AI Framework Production Dashboard",
            "panels": [
                {"title": "Active Agents", "type": "stat", "targets": [{"expr": "ai_framework_agents_active"}]},
                {"title": "API Response Times", "type": "graph", "targets": [{"expr": "ai_framework_api_duration_seconds"}]},
                {"title": "Database Connections", "type": "stat", "targets": [{"expr": "ai_framework_db_connections"}]},
                {"title": "Task Queue Depth", "type": "graph", "targets": [{"expr": "ai_framework_queue_depth"}]},
                {"title": "Error Rate", "type": "graph", "targets": [{"expr": "ai_framework_errors_total"}]},
                {"title": "System Health", "type": "stat", "targets": [{"expr": "ai_framework_services_healthy"}]},
            ],
        }
    }
    config_file = Path("grafana_dashboard.json")
    config_file.write_text(json.dumps(dashboard_config, indent=2), encoding="utf-8")
    print(f"Grafana dashboard config saved to: {config_file}")
    return config_file


def setup_prometheus_config() -> Path:
    prometheus_config = """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-framework'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 5s
"""
    config_file = Path("prometheus.yml")
    config_file.write_text(prometheus_config, encoding="utf-8")
    print(f"Prometheus config saved to: {config_file}")
    return config_file


if __name__ == "__main__":
    setup_grafana_dashboard()
    setup_prometheus_config()



