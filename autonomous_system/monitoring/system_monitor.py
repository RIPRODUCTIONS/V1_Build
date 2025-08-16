"""
System Monitoring and Alerting System

This module provides comprehensive system monitoring and alerting capabilities:
- Real-time system health monitoring
- Performance metrics collection
- Intelligent alerting with escalation
- Resource usage tracking
- Failure detection and recovery
- System status reporting
"""

import asyncio
import json
import logging
import smtplib
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any

import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

@dataclass
class SystemMetric:
    """System performance metric"""
    metric_id: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    threshold_warning: float | None = None
    threshold_critical: float | None = None

@dataclass
class Alert:
    """System alert"""
    alert_id: str
    level: AlertLevel
    status: AlertStatus
    title: str
    description: str
    source: str
    timestamp: datetime
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    escalation_level: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str  # healthy, warning, error, critical
    score: float  # 0.0 to 1.0
    timestamp: datetime
    metrics: dict[str, float]
    alerts: list[Alert]
    recommendations: list[str]

class SystemMonitor:
    """Comprehensive system monitoring and alerting system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get("database", {}).get("path", "system_monitor.db"))
        self._init_database()

        # Monitoring state
        self.active_alerts: dict[str, Alert] = {}
        self.metrics_history: list[SystemMetric] = []
        self.health_history: list[SystemHealth] = []

        # Monitoring configuration
        self.monitoring_interval = config.get("monitoring_interval", 30)  # seconds
        self.alert_escalation_delay = config.get("alert_escalation_delay", 300)  # 5 minutes
        self.max_metrics_history = config.get("max_metrics_history", 10000)
        self.max_health_history = config.get("max_health_history", 1000)

        # Alerting configuration
        self.alert_channels = config.get("alert_channels", {})
        self.escalation_rules = config.get("escalation_rules", {})

        # Thresholds
        self.thresholds = config.get("thresholds", {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 85.0, "critical": 95.0},
            "response_time": {"warning": 2000.0, "critical": 5000.0},
            "error_rate": {"warning": 5.0, "critical": 15.0}
        })

        # Start monitoring
        self._start_monitoring()

    def _init_database(self):
        """Initialize monitoring database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT,
                    threshold_warning REAL,
                    threshold_critical REAL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    escalation_level INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metrics TEXT,
                    alerts_count INTEGER,
                    recommendations TEXT
                )
            """)

            conn.commit()
            conn.close()
            logger.info("System monitor database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize system monitor database: {e}")
            raise

    def _start_monitoring(self):
        """Start system monitoring processes"""
        asyncio.create_task(self._monitor_system_metrics())
        asyncio.create_task(self._monitor_system_health())
        asyncio.create_task(self._process_alerts())
        asyncio.create_task(self._escalate_alerts())
        asyncio.create_task(self._cleanup_old_data())

    async def _monitor_system_metrics(self):
        """Monitor system metrics continuously"""
        while True:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()

                # Store metrics
                for metric in metrics:
                    await self._store_metric(metric)
                    self.metrics_history.append(metric)

                # Check thresholds and generate alerts
                await self._check_thresholds(metrics)

                # Limit history size
                if len(self.metrics_history) > self.max_metrics_history:
                    self.metrics_history = self.metrics_history[-self.max_metrics_history:]

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"System metrics monitoring failed: {e}")
                await asyncio.sleep(60)

    async def _collect_system_metrics(self) -> list[SystemMetric]:
        """Collect current system metrics"""
        metrics = []
        timestamp = datetime.now()

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            metrics.append(SystemMetric(
                metric_id=f"cpu_usage_{int(timestamp.timestamp())}",
                metric_name="cpu_usage",
                value=cpu_percent,
                unit="%",
                timestamp=timestamp,
                category="system",
                threshold_warning=self.thresholds.get("cpu_usage", {}).get("warning"),
                threshold_critical=self.thresholds.get("cpu_usage", {}).get("critical")
            ))

            metrics.append(SystemMetric(
                metric_id=f"cpu_count_{int(timestamp.timestamp())}",
                metric_name="cpu_count",
                value=cpu_count,
                unit="cores",
                timestamp=timestamp,
                category="system"
            ))

            if cpu_freq:
                metrics.append(SystemMetric(
                    metric_id=f"cpu_freq_{int(timestamp.timestamp())}",
                    metric_name="cpu_frequency",
                    value=cpu_freq.current,
                    unit="MHz",
                    timestamp=timestamp,
                    category="system"
                ))

            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(SystemMetric(
                metric_id=f"memory_usage_{int(timestamp.timestamp())}",
                metric_name="memory_usage",
                value=memory.percent,
                unit="%",
                timestamp=timestamp,
                category="system",
                threshold_warning=self.thresholds.get("memory_usage", {}).get("warning"),
                threshold_critical=self.thresholds.get("memory_usage", {}).get("critical")
            ))

            metrics.append(SystemMetric(
                metric_id=f"memory_available_{int(timestamp.timestamp())}",
                metric_name="memory_available",
                value=memory.available / (1024**3),  # Convert to GB
                unit="GB",
                timestamp=timestamp,
                category="system"
            ))

            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics.append(SystemMetric(
                metric_id=f"disk_usage_{int(timestamp.timestamp())}",
                metric_name="disk_usage",
                value=disk.percent,
                unit="%",
                timestamp=timestamp,
                category="system",
                threshold_warning=self.thresholds.get("disk_usage", {}).get("warning"),
                threshold_critical=self.thresholds.get("disk_usage", {}).get("critical")
            ))

            metrics.append(SystemMetric(
                metric_id=f"disk_free_{int(timestamp.timestamp())}",
                metric_name="disk_free",
                value=disk.free / (1024**3),  # Convert to GB
                unit="GB",
                timestamp=timestamp,
                category="system"
            ))

            # Network metrics
            network = psutil.net_io_counters()
            metrics.append(SystemMetric(
                metric_id=f"network_bytes_sent_{int(timestamp.timestamp())}",
                metric_name="network_bytes_sent",
                value=network.bytes_sent / (1024**2),  # Convert to MB
                unit="MB",
                timestamp=timestamp,
                category="network"
            ))

            metrics.append(SystemMetric(
                metric_id=f"network_bytes_recv_{int(timestamp.timestamp())}",
                metric_name="network_bytes_recv",
                value=network.bytes_recv / (1024**2),  # Convert to MB
                timestamp=timestamp,
                category="network"
            ))

            # Process metrics
            process_count = len(psutil.pids())
            metrics.append(SystemMetric(
                metric_id=f"process_count_{int(timestamp.timestamp())}",
                metric_name="process_count",
                value=process_count,
                unit="processes",
                timestamp=timestamp,
                category="system"
            ))

            # Custom metrics (would be injected by other components)
            custom_metrics = await self._collect_custom_metrics()
            metrics.extend(custom_metrics)

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

        return metrics

    async def _collect_custom_metrics(self) -> list[SystemMetric]:
        """Collect custom metrics from other system components"""
        # This would integrate with other components
        # For now, return empty list
        return []

    async def _store_metric(self, metric: SystemMetric):
        """Store metric in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO system_metrics
                (metric_id, metric_name, value, unit, timestamp, category, threshold_warning, threshold_critical)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.metric_id,
                metric.metric_name,
                metric.value,
                metric.unit,
                metric.timestamp,
                metric.category,
                metric.threshold_warning,
                metric.threshold_critical
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store metric: {e}")

    async def _check_thresholds(self, metrics: list[SystemMetric]):
        """Check metrics against thresholds and generate alerts"""
        for metric in metrics:
            if metric.threshold_warning is None and metric.threshold_critical is None:
                continue

            # Check critical threshold first
            if (metric.threshold_critical is not None and
                metric.value >= metric.threshold_critical):
                await self._create_alert(
                    level=AlertLevel.CRITICAL,
                    title=f"Critical {metric.metric_name} threshold exceeded",
                    description=f"{metric.metric_name} is {metric.value}{metric.unit}, exceeding critical threshold of {metric.threshold_critical}{metric.unit}",
                    source=f"system_monitor.{metric.metric_name}",
                    metadata={"metric": metric.__dict__}
                )

            # Check warning threshold
            elif (metric.threshold_warning is not None and
                  metric.value >= metric.threshold_warning):
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    title=f"Warning {metric.metric_name} threshold exceeded",
                    description=f"{metric.metric_name} is {metric.value}{metric.unit}, exceeding warning threshold of {metric.threshold_warning}{metric.unit}",
                    source=f"system_monitor.{metric.metric_name}",
                    metadata={"metric": metric.__dict__}
                )

    async def _create_alert(self, level: AlertLevel, title: str, description: str,
                           source: str, metadata: dict[str, Any] = None):
        """Create a new alert"""
        try:
            alert_id = f"alert_{int(time.time())}_{level.value}"

            alert = Alert(
                alert_id=alert_id,
                level=level,
                status=AlertStatus.ACTIVE,
                title=title,
                description=description,
                source=source,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )

            # Store alert
            await self._store_alert(alert)

            # Add to active alerts
            self.active_alerts[alert_id] = alert

            # Send immediate notification for critical alerts
            if level == AlertLevel.CRITICAL:
                await self._send_alert_notification(alert)

            logger.info(f"Created {level.value} alert: {title}")

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")

    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO alerts
                (alert_id, level, status, title, description, source, timestamp,
                 acknowledged_by, acknowledged_at, resolved_by, resolved_at, escalation_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.level.value,
                alert.status.value,
                alert.title,
                alert.description,
                alert.source,
                alert.timestamp,
                alert.acknowledged_by,
                alert.acknowledged_at,
                alert.resolved_by,
                alert.resolved_at,
                alert.escalation_level,
                json.dumps(alert.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store alert: {e}")

    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while True:
            try:
                # Calculate system health
                health = await self._calculate_system_health()

                # Store health status
                await self._store_system_health(health)
                self.health_history.append(health)

                # Limit history size
                if len(self.health_history) > self.max_health_history:
                    self.health_history = self.health_history[-self.max_health_history:]

                # Generate health-based alerts
                await self._check_health_alerts(health)

                await asyncio.sleep(60)  # Check health every minute

            except Exception as e:
                logger.error(f"System health monitoring failed: {e}")
                await asyncio.sleep(60)

    async def _calculate_system_health(self) -> SystemHealth:
        """Calculate overall system health score"""
        try:
            # Get recent metrics
            recent_metrics = await self._get_recent_metrics(hours=1)

            # Calculate health score based on various factors
            health_score = 1.0
            metrics_summary = {}
            recommendations = []

            # CPU health
            cpu_metrics = [m for m in recent_metrics if m.metric_name == "cpu_usage"]
            if cpu_metrics:
                avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics)
                metrics_summary["cpu_usage"] = avg_cpu

                if avg_cpu > 90:
                    health_score *= 0.3
                    recommendations.append("CPU usage is critically high - consider scaling or optimization")
                elif avg_cpu > 70:
                    health_score *= 0.7
                    recommendations.append("CPU usage is high - monitor closely")

            # Memory health
            memory_metrics = [m for m in recent_metrics if m.metric_name == "memory_usage"]
            if memory_metrics:
                avg_memory = sum(m.value for m in memory_metrics) / len(memory_metrics)
                metrics_summary["memory_usage"] = avg_memory

                if avg_memory > 95:
                    health_score *= 0.2
                    recommendations.append("Memory usage is critically high - immediate action required")
                elif avg_memory > 80:
                    health_score *= 0.6
                    recommendations.append("Memory usage is high - consider cleanup or scaling")

            # Disk health
            disk_metrics = [m for m in recent_metrics if m.metric_name == "disk_usage"]
            if disk_metrics:
                avg_disk = sum(m.value for m in disk_metrics) / len(disk_metrics)
                metrics_summary["disk_usage"] = avg_disk

                if avg_disk > 95:
                    health_score *= 0.1
                    recommendations.append("Disk usage is critically high - immediate cleanup required")
                elif avg_disk > 85:
                    health_score *= 0.5
                    recommendations.append("Disk usage is high - consider cleanup")

            # Alert-based health reduction
            active_alert_count = len(self.active_alerts)
            if active_alert_count > 0:
                critical_alerts = len([a for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL])
                warning_alerts = len([a for a in self.active_alerts.values() if a.level == AlertLevel.WARNING])

                health_score *= (0.5 ** critical_alerts) * (0.8 ** warning_alerts)

                if critical_alerts > 0:
                    recommendations.append(f"Critical alerts active: {critical_alerts} - immediate attention required")
                if warning_alerts > 0:
                    recommendations.append(f"Warning alerts active: {warning_alerts} - monitor closely")

            # Determine overall status
            if health_score >= 0.8:
                status = "healthy"
            elif health_score >= 0.6:
                status = "warning"
            elif health_score >= 0.3:
                status = "error"
            else:
                status = "critical"

            # Add general recommendations
            if health_score < 0.8:
                recommendations.append("Review system performance and implement optimizations")
            if health_score < 0.5:
                recommendations.append("Consider system restart or emergency maintenance")

            health = SystemHealth(
                status=status,
                score=max(0.0, min(1.0, health_score)),
                timestamp=datetime.now(),
                metrics=metrics_summary,
                alerts=list(self.active_alerts.values()),
                recommendations=recommendations
            )

            return health

        except Exception as e:
            logger.error(f"Failed to calculate system health: {e}")
            # Return critical health on error
            return SystemHealth(
                status="critical",
                score=0.0,
                timestamp=datetime.now(),
                metrics={},
                alerts=[],
                recommendations=["System health calculation failed - manual investigation required"]
            )

    async def _store_system_health(self, health: SystemHealth):
        """Store system health in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO system_health
                (status, score, timestamp, metrics, alerts_count, recommendations)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                health.status,
                health.score,
                health.timestamp,
                json.dumps(health.metrics),
                len(health.alerts),
                json.dumps(health.recommendations)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store system health: {e}")

    async def _check_health_alerts(self, health: SystemHealth):
        """Check health status and generate alerts if needed"""
        try:
            if health.status == "critical" and health.score < 0.3:
                await self._create_alert(
                    level=AlertLevel.CRITICAL,
                    title="System health is critical",
                    description=f"System health score is {health.score:.2f} - immediate action required",
                    source="system_monitor.health",
                    metadata={"health": health.__dict__}
                )

            elif health.status == "error" and health.score < 0.5:
                await self._create_alert(
                    level=AlertLevel.ERROR,
                    title="System health is poor",
                    description=f"System health score is {health.score:.2f} - investigation required",
                    source="system_monitor.health",
                    metadata={"health": health.__dict__}
                )

            elif health.status == "warning" and health.score < 0.7:
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    title="System health is degraded",
                    description=f"System health score is {health.score:.2f} - monitor closely",
                    source="system_monitor.health",
                    metadata={"health": health.__dict__}
                )

        except Exception as e:
            logger.error(f"Health alert check failed: {e}")

    async def _process_alerts(self):
        """Process and manage active alerts"""
        while True:
            try:
                # Process active alerts
                for alert_id, alert in list(self.active_alerts.items()):
                    # Check if alert should be escalated
                    if (alert.status == AlertStatus.ACTIVE and
                        alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]):

                        time_since_creation = (datetime.now() - alert.timestamp).total_seconds()
                        if time_since_creation > self.alert_escalation_delay:
                            await self._escalate_alert(alert)

                await asyncio.sleep(30)  # Process alerts every 30 seconds

            except Exception as e:
                logger.error(f"Alert processing failed: {e}")
                await asyncio.sleep(30)

    async def _escalate_alerts(self):
        """Escalate unresolved alerts"""
        while True:
            try:
                # Check for alerts that need escalation
                for alert_id, alert in list(self.active_alerts.items()):
                    if (alert.status == AlertStatus.ACTIVE and
                        alert.escalation_level < 3):  # Max 3 escalation levels

                        time_since_creation = (datetime.now() - alert.timestamp).total_seconds()
                        escalation_threshold = self.alert_escalation_delay * (2 ** alert.escalation_level)

                        if time_since_creation > escalation_threshold:
                            await self._escalate_alert(alert)

                await asyncio.sleep(300)  # Check escalation every 5 minutes

            except Exception as e:
                logger.error(f"Alert escalation failed: {e}")
                await asyncio.sleep(300)

    async def _escalate_alert(self, alert: Alert):
        """Escalate an alert to the next level"""
        try:
            alert.escalation_level += 1
            alert.status = AlertStatus.ESCALATED

            # Update alert in database
            await self._store_alert(alert)

            # Send escalation notification
            await self._send_alert_notification(alert, escalated=True)

            logger.warning(f"Alert {alert.alert_id} escalated to level {alert.escalation_level}")

        except Exception as e:
            logger.error(f"Failed to escalate alert: {e}")

    async def _send_alert_notification(self, alert: Alert, escalated: bool = False):
        """Send alert notification through configured channels"""
        try:
            # Email notifications
            if self.alert_channels.get("email", {}).get("enabled", False):
                await self._send_email_notification(alert, escalated)

            # Slack notifications
            if self.alert_channels.get("slack", {}).get("enabled", False):
                await self._send_slack_notification(alert, escalated)

            # Webhook notifications
            if self.alert_channels.get("webhook", {}).get("enabled", False):
                await self._send_webhook_notification(alert, escalated)

            # Log notification
            if escalated:
                logger.critical(f"ESCALATED ALERT: {alert.title} - {alert.description}")
            else:
                logger.warning(f"ALERT: {alert.title} - {alert.description}")

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

    async def _send_email_notification(self, alert: Alert, escalated: bool):
        """Send email notification"""
        try:
            email_config = self.alert_channels.get("email", {})

            if not email_config.get("enabled", False):
                return

            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config.get("from_email", "noreply@system.com")
            msg['To'] = email_config.get("to_email", "admin@system.com")

            if escalated:
                msg['Subject'] = f"🚨 ESCALATED: {alert.title}"
            else:
                msg['Subject'] = f"⚠️ {alert.title}"

            # Create email body
            body = f"""
            Alert Details:
            --------------
            Level: {alert.level.value.upper()}
            Status: {alert.status.value}
            Source: {alert.source}
            Time: {alert.timestamp}
            Escalation Level: {alert.escalation_level}

            Description:
            {alert.description}

            Actions Required:
            - Acknowledge the alert
            - Investigate the issue
            - Implement corrective measures
            - Resolve the alert when fixed

            System: Autonomous Task Solver
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(email_config.get("smtp_server", "localhost"))
            if email_config.get("use_tls", False):
                server.starttls()

            if email_config.get("username") and email_config.get("password"):
                server.login(email_config["username"], email_config["password"])

            server.send_message(msg)
            server.quit()

            logger.info(f"Email notification sent for alert {alert.alert_id}")

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    async def _send_slack_notification(self, alert: Alert, escalated: bool):
        """Send Slack notification"""
        # This would integrate with Slack API
        # For now, just log the attempt
        logger.info(f"Slack notification would be sent for alert {alert.alert_id}")

    async def _send_webhook_notification(self, alert: Alert, escalated: bool):
        """Send webhook notification"""
        # This would send HTTP POST to configured webhook
        # For now, just log the attempt
        logger.info(f"Webhook notification would be sent for alert {alert.alert_id}")

    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        while True:
            try:
                # Clean up old metrics (keep last 7 days)
                await self._cleanup_old_metrics(days=7)

                # Clean up old health data (keep last 30 days)
                await self._cleanup_old_health_data(days=30)

                # Clean up resolved alerts (keep last 90 days)
                await self._cleanup_old_alerts(days=90)

                await asyncio.sleep(3600)  # Cleanup every hour

            except Exception as e:
                logger.error(f"Data cleanup failed: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_old_metrics(self, days: int):
        """Clean up old metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(days=days)

            cursor.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff_time,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old metrics")

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")

    async def _cleanup_old_health_data(self, days: int):
        """Clean up old health data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(days=days)

            cursor.execute("DELETE FROM system_health WHERE timestamp < ?", (cutoff_time,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old health records")

        except Exception as e:
            logger.error(f"Failed to cleanup old health data: {e}")

    async def _cleanup_old_alerts(self, days: int):
        """Clean up old resolved alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(days=days)

            cursor.execute("DELETE FROM alerts WHERE resolved_at < ? AND status = 'resolved'", (cutoff_time,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old resolved alerts")

        except Exception as e:
            logger.error(f"Failed to cleanup old alerts: {e}")

    # Public API methods
    async def get_system_status(self) -> dict[str, Any]:
        """Get current system status"""
        try:
            # Get latest health
            latest_health = self.health_history[-1] if self.health_history else None

            # Get active alerts count by level
            alert_counts = {}
            for level in AlertLevel:
                alert_counts[level.value] = len([a for a in self.active_alerts.values() if a.level == level])

            # Get recent metrics summary
            recent_metrics = await self._get_recent_metrics(hours=1)
            metrics_summary = {}

            for metric in recent_metrics:
                if metric.metric_name not in metrics_summary:
                    metrics_summary[metric.metric_name] = {
                        'current': metric.value,
                        'unit': metric.unit,
                        'category': metric.category
                    }

            status = {
                'timestamp': datetime.now().isoformat(),
                'health': latest_health.__dict__ if latest_health else None,
                'alerts': {
                    'total_active': len(self.active_alerts),
                    'by_level': alert_counts
                },
                'metrics': metrics_summary,
                'monitoring': {
                    'interval_seconds': self.monitoring_interval,
                    'max_metrics_history': self.max_metrics_history,
                    'max_health_history': self.max_health_history
                }
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False

            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()

            # Update in database
            await self._store_alert(alert)

            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True

        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False

    async def resolve_alert(self, alert_id: str, resolved_by: str, resolution_notes: str = "") -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False

            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.now()

            # Add resolution notes to metadata
            if not alert.metadata:
                alert.metadata = {}
            alert.metadata['resolution_notes'] = resolution_notes
            alert.metadata['resolution_time'] = datetime.now().isoformat()

            # Update in database
            await self._store_alert(alert)

            # Remove from active alerts
            del self.active_alerts[alert_id]

            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True

        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False

    async def get_alerts(self, status: AlertStatus | None = None,
                        level: AlertLevel | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get alerts with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM alerts WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if level:
                query += " AND level = ?"
                params.append(level.value)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            alerts = []
            for row in rows:
                alert_dict = {
                    'alert_id': row[0],
                    'level': row[1],
                    'status': row[2],
                    'title': row[3],
                    'description': row[4],
                    'source': row[5],
                    'timestamp': row[6],
                    'acknowledged_by': row[7],
                    'acknowledged_at': row[8],
                    'resolved_by': row[9],
                    'resolved_at': row[10],
                    'escalation_level': row[11],
                    'metadata': json.loads(row[12]) if row[12] else {}
                }
                alerts.append(alert_dict)

            conn.close()
            return alerts

        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    async def _get_recent_metrics(self, hours: int) -> list[SystemMetric]:
        """Get recent metrics from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT * FROM system_metrics
                WHERE timestamp > ? ORDER BY timestamp DESC
            """, (cutoff_time,))

            rows = cursor.fetchall()
            metrics = []

            for row in rows:
                metric = SystemMetric(
                    metric_id=row[0],
                    metric_name=row[1],
                    value=row[2],
                    unit=row[3],
                    timestamp=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    category=row[5],
                    threshold_warning=row[6],
                    threshold_critical=row[7]
                )
                metrics.append(metric)

            conn.close()
            return metrics

        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []


# Example usage
async def main():
    """Example usage of the system monitor"""
    config = {
        "database": {"path": "test_system_monitor.db"},
        "monitoring_interval": 10,
        "alert_escalation_delay": 60,
        "max_metrics_history": 1000,
        "max_health_history": 100,
        "thresholds": {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 85.0, "critical": 95.0}
        },
        "alert_channels": {
            "email": {
                "enabled": False,
                "smtp_server": "localhost",
                "from_email": "noreply@system.com",
                "to_email": "admin@system.com"
            },
            "slack": {"enabled": False},
            "webhook": {"enabled": False}
        }
    }

    monitor = SystemMonitor(config)

    # Wait for some monitoring data
    await asyncio.sleep(15)

    # Get system status
    status = await monitor.get_system_status()
    print("System Status:", json.dumps(status, indent=2, default=str))

    # Get alerts
    alerts = await monitor.get_alerts(limit=10)
    print("Alerts:", json.dumps(alerts, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
