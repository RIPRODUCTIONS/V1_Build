#!/usr/bin/env python3
"""
AI Framework Production Server

A robust, production-ready server with:
- Proper error handling and recovery
- Health checks and monitoring
- Graceful shutdown
- Resource management
- Logging and metrics
"""

import asyncio
import logging
import os
import signal
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

import redis.asyncio as redis

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from typing import Any

from diagnostics.system_diagnostics import report_to_markdown, run_diagnostics
from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from scaling.bootstrap_700_agents import bootstrap_700_agents
from scaling.continuous_task_seeder import ContinuousTaskSeeder
from scaling.enhanced_metrics import active_workers
from scaling.partitioned_queue import PartitionedQueueManager
from scaling.scaled_worker_manager import ScaledWorkerManager
from starlette.middleware.base import BaseHTTPMiddleware

from core.agent_orchestrator import AgentOrchestrator
from core.browser_operator import BrowserOperator
from core.correlation import CorrelationIDMiddleware
from core.db import (
    init_db,
)
from core.master_dashboard import MasterDashboard
from core.scheduler import Scheduler
from monitoring.metrics_collector import MetricsCollector

# Optional integrations and seeds are imported at top-level (to avoid in-function imports)
try:
    KALI_AVAILABLE = True
except Exception:
    KALI_AVAILABLE = False

try:
    WORKLOAD_SEEDS_AVAILABLE = True
except Exception:
    WORKLOAD_SEEDS_AVAILABLE = False

try:
    CONTINUOUS_SEEDS_AVAILABLE = True
except Exception:
    CONTINUOUS_SEEDS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_framework.log')
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("ai_framework_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("ai_framework_http_request_latency_seconds", "HTTP request latency", buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5))

class InMemoryRateLimiter:
    def __init__(self, limit_per_minute: int = 120):
        self.limit = limit_per_minute
        self._window_start = 0
        self._counts: dict[str, int] = {}

    def allow(self, key: str) -> bool:
        now = int(time.time())
        window = now // 60
        if window != self._window_start:
            self._window_start = window
            self._counts.clear()
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        return count <= self.limit

rate_limiter = InMemoryRateLimiter(limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MIN", "120")))
API_KEY_ENV = os.environ.get("API_KEY")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALG = os.environ.get("JWT_ALG", "HS256")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
MAX_TASK_ATTEMPTS = int(os.environ.get("MAX_TASK_ATTEMPTS", "3"))

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health checks and request logging."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Basic request log
        logger.info(f"{request.method} {request.url.path}")

        # Simple IP-based rate limiting (skip metrics and health)
        path = request.url.path
        if not path.startswith("/metrics"):
            client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
            if not rate_limiter.allow(client_ip):
                REQUEST_COUNT.labels(request.method, path, str(429)).inc()
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        try:
            response = await call_next(request)
            latency = time.time() - start_time
            REQUEST_LATENCY.observe(latency)
            REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
            response.headers["X-Process-Time"] = str(latency)
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            REQUEST_COUNT.labels(request.method, path, str(500)).inc()
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(e)}
            )

class AIFrameworkServer:
    """Production-ready AI Framework server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8001, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.app = None
        self.server = None
        self.shutdown_event = asyncio.Event()

        # Initialize components
        self.dashboard = None
        self.orchestrator = None
        self.ws_connections: list[WebSocket] = []
        self.broadcast_task: asyncio.Task | None = None
        self.metrics_task: asyncio.Task | None = None
        self.worker_task: asyncio.Task | None = None
        self.scheduler: Scheduler | None = None
        self.sla_task: asyncio.Task | None = None

        # Enterprise monitoring and scaling services
        self.enterprise_alert_task: asyncio.Task | None = None
        self.enterprise_metrics_task: asyncio.Task | None = None
        self.alert_manager: Any = None
        self.metrics_collector: Any = None
        self.simple_scale700: Any = None  # optional lightweight manager

        # Scale-700 components (feature-flagged)
        self.scale_enabled: bool = os.environ.get("ENABLE_SCALE700", "0") == "1"
        self.scale_redis: redis.Redis | None = None
        self.scale_registry = None
        self.scale_queue_manager = None
        self.scale_worker_manager = None
        self.scale_seeder = None
        self.scale_seeder_task: asyncio.Task | None = None
        self.scale_monitor_task: asyncio.Task | None = None

        # Optional Browser Operator (feature-flagged)
        self.browser_operator = None

        # Setup signal handlers
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _initialize_components(self):
        """Initialize AI Framework components with proper error handling."""
        try:
            logger.info("🔧 Initializing AI Framework components...")

            # Initialize DB
            try:
                init_db()
                logger.info("✅ Database initialized")
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}")

            # Initialize components

            # Initialize orchestrator
            logger.info("📡 Initializing Agent Orchestrator...")
            self.orchestrator = AgentOrchestrator()
            logger.info("✅ Agent Orchestrator initialized")

            # Initialize dashboard
            logger.info("🎛️ Initializing Master Dashboard...")
            self.dashboard = MasterDashboard(self.orchestrator)
            logger.info("✅ Master Dashboard initialized")

            # Initialize optional Browser Operator
            try:
                data_dir = Path(__file__).parent / "browser_data"
                self.browser_operator = BrowserOperator(data_dir)
                logger.info("🧭 Browser Operator initialized (ENABLE_BROWSER_OPERATOR controls availability)")
            except Exception as e:
                logger.info(f"Browser Operator unavailable: {e}")

            # Run health check
            logger.info("🏥 Running component health check...")
            await self._health_check()
            logger.info("✅ Component health check passed")

            # Initialize enterprise metrics collector (always available)
            try:
                self.metrics_collector = MetricsCollector()
            except Exception:
                self.metrics_collector = None

            return True

        except Exception as e:
            logger.error(f"❌ Component initialization failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def _health_check(self):
        """Run comprehensive health check."""
        if not self.dashboard:
            raise Exception("Dashboard not initialized")

        overview = await self.dashboard.get_dashboard_overview()
        total_agents = overview['overview']['total_agents']
        active_agents = overview['overview']['active_agents']

        if total_agents != active_agents:
            raise Exception(f"Agent mismatch: {active_agents}/{total_agents} agents active")

        logger.info(f"✅ Health check passed: {active_agents}/{total_agents} agents active")

    async def _start_scale700(self):
        """Start optional 700-agent scaling stack behind feature flag."""
        try:
            if not self.scale_enabled:
                return
            logger.info("⚙️ Starting Scale-700 components (feature-flag ENABLE_SCALE700=1)")
            # Initialize scaling components

            redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
            self.scale_redis = redis.from_url(redis_url)

            # Bootstrap 700 logical agents (separate registry from dashboard's agents)
            self.scale_registry = bootstrap_700_agents()

            # Queue manager and workers
            self.scale_queue_manager = PartitionedQueueManager(self.scale_redis)
            self.scale_worker_manager = ScaledWorkerManager(self.scale_queue_manager, self.scale_registry)
            await self.scale_worker_manager.start_all_workers()

            # Seeder
            self.scale_seeder = ContinuousTaskSeeder(self.scale_queue_manager, self.scale_registry)
            self.scale_seeder_task = asyncio.create_task(self.scale_seeder.start_continuous_seeding())

            # Monitor metrics
            async def _scale_monitor():
                while not self.shutdown_event.is_set():
                    try:
                        depths = await self.scale_queue_manager.get_queue_depths()
                        for domain, depth in depths.items():
                            MetricsCollector.update_queue_depth("default", domain.value, 0, depth)
                        for domain, procs in (self.scale_worker_manager.worker_processes or {}).items():
                            alive = sum(1 for p in procs if p.is_alive())
                            active_workers.labels(domain=domain.value).set(alive)
                        await asyncio.sleep(15)
                    except asyncio.CancelledError:
                        break
                    except Exception:
                        await asyncio.sleep(30)
            self.scale_monitor_task = asyncio.create_task(_scale_monitor())
            logger.info("✅ Scale-700 components started")
        except Exception as e:
            logger.warning(f"Scale-700 startup skipped due to error: {e}")

    def _create_fastapi_app(self):
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="AI Framework Backend",
            description="Production-ready backend for the AI Framework with 50+ specialized agents",
            version="2.0.0",
            docs_url="/docs" if self.debug else None,
            redoc_url="/redoc" if self.debug else None
        )

        # Add middleware
        app.add_middleware(HealthCheckMiddleware)
        app.add_middleware(CorrelationIDMiddleware)

        # CORS configuration (hardened via env)
        allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
        allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        # Trusted host middleware for production (via env)
        trusted_hosts_env = os.environ.get("TRUSTED_HOSTS", "*")
        trusted_hosts = [h.strip() for h in trusted_hosts_env.split(",") if h.strip()]
        if not self.debug:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=trusted_hosts
            )

        # Mount static files
        frontend_path = Path(__file__).parent / "frontend"
        if frontend_path.exists():
            app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

        # Add routes
        self._add_routes(app)

        return app

    def _require_auth(self, request: Request, api_key: str | None = Header(default=None, alias="X-API-Key")):
        """Dependency to enforce API key or JWT if configured.
        - If API_KEY is set, accept matching X-API-Key
        - If JWT_SECRET is set, accept valid Authorization: Bearer <jwt>
        If neither is set, allow (dev mode).
        """
        # If neither configured → allow
        if not API_KEY_ENV and not JWT_SECRET:
            return
        # API key path
        if API_KEY_ENV and api_key == API_KEY_ENV:
            return
        # JWT path
        if JWT_SECRET:
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                try:
                    jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
                    return
                except JWTError:
                    pass
        raise HTTPException(status_code=401, detail="Unauthorized")

    def _add_routes(self, app: FastAPI):
        """Add all API routes to the FastAPI app."""
        self._add_basic_routes(app)
        self._add_api_routes(app)
        self._add_metrics_routes(app)
        self._add_diagnostics_routes(app)
        self._add_agent_routes(app)
        self._add_system_routes(app)

    def _add_basic_routes(self, app: FastAPI):
        """Add basic routes like root, health, and ready."""
        @app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "AI Framework Backend", "status": "running"}

        @app.get("/health")
        async def health():
            """Health check endpoint."""
            try:
                if self.dashboard:
                    overview = await self.dashboard.get_dashboard_overview()
                    return {
                        "status": "healthy",
                        "agents": overview['overview']['total_agents'],
                        "departments": len(overview['departments']),
                        "timestamp": time.time()
                    }
                else:
                    return {"status": "initializing", "timestamp": time.time()}
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}

        @app.get("/ready")
        async def ready():
            """Readiness probe: ensures components are initialized."""
            try:
                if not self.dashboard:
                    raise Exception("dashboard not initialized")
                overview = await self.dashboard.get_dashboard_overview()
                if overview['overview']['total_agents'] <= 0:
                    raise Exception("no agents loaded")
                return {"status": "ready", "timestamp": time.time()}
            except Exception as e:
                return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})

    def _add_api_routes(self, app: FastAPI):
        """Add API-specific routes."""
        self._add_queue_metrics_route(app)
        self._add_diagnostics_routes(app)
        self._add_prometheus_metrics_route(app)

    def _add_queue_metrics_route(self, app: FastAPI):
        """Add queue metrics route."""
        @app.get("/metrics/queues")
        async def metrics_queues():
            """Return current queue depths for domain partitions if Scale-700 is enabled."""
            try:
                depths = {}
                total = 0
                if self.scale_enabled and self.scale_queue_manager is not None:
                    qd = await self.scale_queue_manager.get_queue_depths()
                    depths = {d.value: v for d, v in qd.items()}
                    total = sum(qd.values())
                return {
                    "queue_depths": depths,
                    "total_queued": total,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

    def _add_diagnostics_routes(self, app: FastAPI):
        """Add diagnostics-related routes."""
        @app.get("/api/diagnostics", dependencies=[Depends(self._require_auth)])
        async def api_diagnostics():
            try:
                return await run_diagnostics(self)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

        @app.get("/api/diagnostics/diagram", dependencies=[Depends(self._require_auth)])
        async def api_diagnostics_diagram():
            try:
                data = await run_diagnostics(self)
                return PlainTextResponse(content=data.get("mermaid", ""), media_type="text/plain")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

        @app.get("/api/diagnostics/report", dependencies=[Depends(self._require_auth)])
        async def api_diagnostics_report():
            try:
                data = await run_diagnostics(self)
                md = report_to_markdown(data)
                return PlainTextResponse(content=md, media_type="text/markdown")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

    def _add_prometheus_metrics_route(self, app: FastAPI):
        """Add Prometheus metrics route."""
        @app.get("/metrics/prometheus")
        async def metrics_prometheus():
            try:
                # Base system
                base = {}
                if self.metrics_collector:
                    base = await self.metrics_collector.collect_system_metrics()
                lines: list[str] = []
                if base:
                    lines.append(f"ai_framework_cpu_percent {base['system']['cpu_percent']}")
                    lines.append(f"ai_framework_memory_percent {base['system']['memory_percent']}")
                    lines.append(f"ai_framework_disk_percent {base['system']['disk_percent']}")
                    lines.append(f"ai_framework_tasks_total {base['tasks']['total']}")
                    lines.append(f"ai_framework_tasks_pending {base['tasks']['pending']}")
                    lines.append(f"ai_framework_tasks_running {base['tasks']['running']}")
                    lines.append(f"ai_framework_tasks_completed_total {base['tasks']['completed']}")
                    lines.append(f"ai_framework_tasks_failed_total {base['tasks']['failed']}")
                    if 'agents' in base:
                        lines.append(f"ai_framework_agents_active {base['agents'].get('active', 0)}")
                        lines.append(f"ai_framework_departments_total {base['agents'].get('departments', 0)}")
                
                # Scale-700 queue depths
                if self.scale_enabled and self.scale_queue_manager is not None:
                    try:
                        depths = await self.scale_queue_manager.get_queue_depths()
                        for d, v in depths.items():
                            lines.append(f'ai_framework_queue_depth{{department="{d.value}"}} {v}')
                    except Exception:
                        pass
                elif self.simple_scale700 is not None:
                    try:
                        for dept, qname in self.simple_scale700.department_queues.items():
                            try:
                                depth = await self.simple_scale700.redis.llen(qname)
                                lines.append(f'ai_framework_queue_depth{{department="{dept}"}} {depth}')
                            except Exception:
                                continue
                    except Exception:
                        pass
                
                # Services health
                lines.append(f"ai_framework_services_healthy {1 if (self.enterprise_alert_task or self.enterprise_metrics_task) else 0}")
                return Response(content="\n".join(lines) + "\n", media_type="text/plain")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

    def _add_metrics_routes(self, app: FastAPI):
        """Add metrics-related routes."""
        @app.get("/metrics")
        async def metrics():
            data = generate_latest()
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)

        # Prometheus exposition for Grafana scrape (complements /metrics JSON)
        @app.get("/metrics/prometheus")
        async def metrics_prometheus():
            try:
                # Base system
                base = {}
                if self.metrics_collector:
                    base = await self.metrics_collector.collect_system_metrics()
                lines: list[str] = []
                if base:
                    if "system" in base and "cpu_percent" in base["system"]:
                        lines.append("ai_framework_cpu_percent " + str(base["system"]["cpu_percent"]))
                    if "system" in base and "memory_percent" in base["system"]:
                        lines.append("ai_framework_memory_percent " + str(base["system"]["memory_percent"]))
                    if "system" in base and "disk_percent" in base["system"]:
                        lines.append("ai_framework_disk_percent " + str(base["system"]["disk_percent"]))

                return PlainTextResponse(content="\n".join(lines), media_type="text/plain")

            except Exception as e:
                logging.error(f"Metrics collection failed: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        return True


if __name__ == "__main__":
    import asyncio
    server = AIFrameworkServer()
    asyncio.run(server.start())
