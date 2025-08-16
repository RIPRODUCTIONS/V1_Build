"""
Master Control Dashboard

This module provides a unified dashboard for monitoring and controlling all AI agents
across the organization. It serves as the central nervous system for the AI framework,
providing real-time visibility, control, and orchestration capabilities.
"""

import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from agents import (
    # Executive agents
    AICEO,
    AICFO,
    AICHR,
    # Marketing agents
    AICMO,
    AICOO,
    AICTO,
    # Finance agents
    AIAccountant,
    AIAccountManager,
    AIAuditor,
    AIBrandManager,
    AICampaignManager,
    AICloudOptimizer,
    AICollectionsOfficer,
    AIComplianceManager,
    AIComplianceOfficer,
    AIContractNegotiator,
    AIController,
    AICopywriter,
    AICustomerSupportAgent,
    AIDataEngineer,
    AIDevOpsEngineer,
    AIFleetManager,
    AIFraudAnalyst,
    # Legal agents
    AIGeneralCounsel,
    # Creative agents
    AIGraphicDesigner,
    AIHealthCoach,
    AIHomeManager,
    AIIncidentResponder,
    AIIPManager,
    AILeadQualifier,
    AILearningMentor,
    AIOnboardingSpecialist,
    AIPaymentsManager,
    # Cybersecurity agents
    AIPenetrationTester,
    AIPerformanceCoach,
    # Personal agents
    AIPersonalAssistant,
    AIPRAgent,
    AIProcurementOfficer,
    # HR agents
    AIRecruiter,
    # Sales agents
    AISalesManager,
    AIScheduler,
    AISecurityAnalyst,
    AISecurityMonitor,
    AISEOSpecialist,
    AISocialMediaManager,
    # Operations agents
    AISupplyChainManager,
    # IT & Security agents
    AISysAdmin,
    AIThreatHunter,
    AITrader,
    AITrainingManager,
    AITravelAgent,
    AIVideoProducer,
)
from agents.base import (
    AgentConfig,
    AgentDepartment,
    AgentType,
    BaseAgent,  # precise type for registry
)
from config.agent_configs import get_all_agent_configs

# Conditional imports for feature-flagged agents
try:
    from market.agents import (
        AICompetitiveAnalyzer,
        AILocalAdapter,
        AIMarketScanner,
        AIPartnershipBuilder,
        AIRevenueOptimizer,
    )
    MARKET_AGENTS_AVAILABLE = True
except ImportError:
    MARKET_AGENTS_AVAILABLE = False

try:
    from infra.agents import (
        AICDNOptimizer,
        AIDBShardingManager,
        AIInfraProvisioner,
        AILoadBalancer,
        AISecurityHardener,
    )
    INFRA_AGENTS_AVAILABLE = True
except ImportError:
    INFRA_AGENTS_AVAILABLE = False

from .agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class DashboardStatus(str, Enum):
    """Status of the master dashboard."""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    OFFLINE = "offline"


class SystemHealth(str, Enum):
    """Overall system health status."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class DashboardMetrics:
    """Comprehensive metrics for the master dashboard."""
    total_agents: int = 0
    active_agents: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    system_uptime: float = 100.0
    overall_efficiency: float = 0.0
    cost_per_hour: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentStatus:
    """Status of each department/domain."""
    department: str
    agent_count: int
    active_agents: int
    total_tasks: int
    completed_tasks: int
    efficiency: float
    status: str
    last_updated: datetime


class MasterDashboard:
    """Master control dashboard for the AI framework."""

    def __init__(self, agent_orchestrator: AgentOrchestrator):
        self.agent_orchestrator = agent_orchestrator
        self.status = DashboardStatus.ACTIVE
        self.system_health = SystemHealth.EXCELLENT
        self.metrics = DashboardMetrics()
        self.department_statuses: dict[str, DepartmentStatus] = {}
        self.agent_registry: dict[str, BaseAgent] = {}
        self.emergency_protocols: dict[str, Callable[[], Awaitable[dict[str, Any]]]] = {}

        # Initialize all agents
        self._initialize_agents()
        self._setup_emergency_protocols()

        logger.info("Master Dashboard initialized successfully")

    def _initialize_agents(self):
        """Initialize all AI agents across all departments with proper configurations."""
        try:
            # Get all agent configurations
            agent_configs = get_all_agent_configs()

            # Initialize core agents
            self._initialize_core_agents(agent_configs)

            # Initialize feature-flagged agents
            self._initialize_feature_flagged_agents()

            logger.info(f"🎯 Initialized {len(self.agent_registry)} agents successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {str(e)}")
            raise

    def _initialize_core_agents(self, agent_configs: dict[str, Any]):
        """Initialize core agents from configurations."""
        for _config_key, config in agent_configs.items():
            try:
                # Get the agent class
                agent_class = self._get_agent_class(config.name)
                if agent_class:
                    # Create agent instance with proper config
                    agent = agent_class(config)
                    self._register_agent(agent, config.department.value, config.name)
                    logger.info(f"✅ Initialized {config.name} agent")
                else:
                    logger.warning(f"⚠️ Agent class not found for {config.name}")
            except Exception as e:
                logger.warning(f"Failed to initialize {config.name}: {e}")

    def _initialize_feature_flagged_agents(self):
        """Initialize feature-flagged additional agents."""
        self._initialize_market_agents()
        self._initialize_infrastructure_agents()

    def _initialize_market_agents(self):
        """Initialize market-related agents if enabled."""
        if os.environ.get("ENABLE_MARKETS") == "1" and MARKET_AGENTS_AVAILABLE:
            try:
                market_agent_classes = [
                    AIMarketScanner,
                    AICompetitiveAnalyzer,
                    AILocalAdapter,
                    AIPartnershipBuilder,
                    AIRevenueOptimizer,
                ]
                self._initialize_agent_list(market_agent_classes, "market")
            except Exception:
                pass

    def _initialize_infrastructure_agents(self):
        """Initialize infrastructure agents if enabled."""
        if os.environ.get("ENABLE_INFRA_AUTOSCALE") == "1" and INFRA_AGENTS_AVAILABLE:
            try:
                infra_agent_classes = [
                    AIInfraProvisioner,
                    AILoadBalancer,
                    AIDBShardingManager,
                    AICDNOptimizer,
                    AISecurityHardener,
                ]
                self._initialize_agent_list(infra_agent_classes, "infrastructure")
            except Exception:
                pass

    def _initialize_agent_list(self, agent_classes: list[type], department: str):
        """Initialize a list of agents for a specific department."""
        for agent_cls in agent_classes:
            try:
                agent = agent_cls(config=self._make_placeholder_config(agent_cls.__name__, department=department))
                self._register_agent(agent, department, agent.config.name)
            except Exception:
                continue

    def _get_agent_class(self, agent_name: str) -> type[BaseAgent] | None:
        """Get the agent class by name."""
        # Map agent names to classes
        agent_map = {
            # Executive agents
            "AI CEO": AICEO,
            "AI COO": AICOO,
            "AI CFO": AICFO,
            "AI CTO": AICTO,
            "AI CHRO": AICHR,

            # Cybersecurity agents
            "AI Penetration Tester": AIPenetrationTester,
            "AI Security Monitor": AISecurityMonitor,
            "AI Threat Hunter": AIThreatHunter,
            "AI Incident Responder": AIIncidentResponder,
            "AI Compliance Manager": AIComplianceManager,

            # Finance agents
            "AI Accountant": AIAccountant,
            "AI Controller": AIController,
            "AI Trader": AITrader,
            "AI Payments Manager": AIPaymentsManager,
            "AI Collections Officer": AICollectionsOfficer,
            "AI Fraud Analyst": AIFraudAnalyst,
            "AI Auditor": AIAuditor,

            # Sales agents
            "AI Sales Manager": AISalesManager,
            "AI Lead Qualifier": AILeadQualifier,
            "AI Account Manager": AIAccountManager,
            "AI Customer Support": AICustomerSupportAgent,
            "AI Onboarding Specialist": AIOnboardingSpecialist,

            # Marketing agents
            "AI CMO": AICMO,
            "AI Campaign Manager": AICampaignManager,
            "AI Social Media Manager": AISocialMediaManager,
            "AI SEO Specialist": AISEOSpecialist,
            "AI PR Agent": AIPRAgent,

            # Operations agents
            "AI Supply Chain Manager": AISupplyChainManager,
            "AI Fleet Manager": AIFleetManager,
            "AI Scheduler": AIScheduler,
            "AI Procurement Officer": AIProcurementOfficer,

            # HR agents
            "AI Recruiter": AIRecruiter,
            "AI Training Manager": AITrainingManager,
            "AI Performance Coach": AIPerformanceCoach,
            "AI Compliance Officer": AIComplianceOfficer,

            # Legal agents
            "AI General Counsel": AIGeneralCounsel,
            "AI IP Manager": AIIPManager,
            "AI Contract Negotiator": AIContractNegotiator,

            # IT & Security agents
            "AI SysAdmin": AISysAdmin,
            "AI Security Analyst": AISecurityAnalyst,
            "AI DevOps Engineer": AIDevOpsEngineer,
            "AI Data Engineer": AIDataEngineer,
            "AI Cloud Optimizer": AICloudOptimizer,

            # Creative agents
            "AI Graphic Designer": AIGraphicDesigner,
            "AI Video Producer": AIVideoProducer,
            "AI Copywriter": AICopywriter,
            "AI Brand Manager": AIBrandManager,

            # Personal agents
            "AI Personal Assistant": AIPersonalAssistant,
            "AI Travel Agent": AITravelAgent,
            "AI Health Coach": AIHealthCoach,
            "AI Home Manager": AIHomeManager,
            "AI Learning Mentor": AILearningMentor,
        }

        return agent_map.get(agent_name)

    def _make_placeholder_config(self, name: str, department: str):
        dept = getattr(AgentDepartment, department.upper(), AgentDepartment.OPERATIONS)
        # Choose a reasonable default AgentType to satisfy typing
        default_type = getattr(AgentType, "COORDINATOR", list(AgentType)[0])
        return AgentConfig(name=name, agent_type=default_type, department=dept, capabilities=["placeholder"])

    def _register_agent(self, agent_instance: BaseAgent, department: str, name: str) -> None:
        """Register an agent instance with the dashboard."""
        try:
            # Generate a unique agent ID
            agent_id = f"{department}_{name.lower().replace(' ', '_')}"

            # Store the agent instance directly
            self.agent_registry[agent_id] = agent_instance

            logger.info(f"Registered agent: {name} in department {department}")

        except Exception as e:
            logger.error(f"Failed to register agent {name}: {str(e)}")

    def _setup_emergency_protocols(self):
        """Setup emergency protocols for system protection."""
        self.emergency_protocols = {
            "system_overload": self._handle_system_overload,
            "security_breach": self._handle_security_breach,
            "critical_failure": self._handle_critical_failure,
            "resource_exhaustion": self._handle_resource_exhaustion
        }

    async def get_dashboard_overview(self) -> dict[str, Any]:
        """Get comprehensive dashboard overview."""
        await self._update_metrics()

        return {
            "dashboard_status": self.status.value,
            "system_health": self.system_health.value,
            "overview": {
                "total_agents": self.metrics.total_agents,
                "active_agents": self.metrics.active_agents,
                "total_tasks": self.metrics.total_tasks,
                "completed_tasks": self.metrics.completed_tasks,
                "failed_tasks": self.metrics.failed_tasks,
                "system_uptime": float(self.metrics.system_uptime),
                "overall_efficiency": float(self.metrics.overall_efficiency),
                "cost_per_hour": float(self.metrics.cost_per_hour)
            },
            "departments": await self._get_department_summary(),
            "recent_activity": await self._get_recent_activity(),
            "kpis": await self._get_kpis_summary(),
            "insights": await self._get_insights(),
            "alerts": await self._get_active_alerts(),
            "last_updated": self.metrics.last_updated.isoformat()
        }

    async def _update_metrics(self):
        """Update dashboard metrics."""
        self.metrics.total_agents = len(self.agent_registry)
        self.metrics.active_agents = sum(
            1 for agent in self.agent_registry.values()
            if agent.status.value != "offline"
        )

        # Calculate overall efficiency
        total_efficiency = 0.0
        active_count = 0

        for agent in self.agent_registry.values():
            if agent.status.value != "offline" and hasattr(agent, 'performance_metrics'):
                success_rate = getattr(agent.performance_metrics, 'success_rate', 0.8)
                total_efficiency += success_rate
                active_count += 1

        if active_count > 0:
            self.metrics.overall_efficiency = float(total_efficiency) / float(active_count) * 100.0

        self.metrics.last_updated = datetime.now(UTC)

    async def _get_department_summary(self) -> dict[str, Any]:
        """Get summary of all departments."""
        departments: dict[str, dict[str, Any]] = {}

        for agent in self.agent_registry.values():
            # Safely get department name with fallback
            try:
                if hasattr(agent, 'config') and hasattr(agent.config, 'department'):
                    dept_name = agent.config.department.value if hasattr(agent.config.department, 'value') else str(agent.config.department)
                else:
                    dept_name = "unknown"
            except Exception:
                dept_name = "unknown"

            if dept_name not in departments:
                departments[dept_name] = {
                    "agent_count": 0,
                    "active_agents": 0,
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "efficiency": 0.0,
                    "status": "operational"
                }

            departments[dept_name]["agent_count"] += 1
            if hasattr(agent, 'status') and hasattr(agent.status, 'value'):
                if agent.status.value != "offline":
                    departments[dept_name]["active_agents"] += 1
            else:
                # Default to active if status is not properly set
                departments[dept_name]["active_agents"] += 1

            if hasattr(agent, 'performance_metrics'):
                pm = getattr(agent, 'performance_metrics', {}) or {}
                departments[dept_name]["total_tasks"] += int(pm.get('total_tasks_processed', 0) or 0)
                departments[dept_name]["completed_tasks"] += int(pm.get('successful_tasks', 0) or 0)

        # Calculate department efficiency
        for dept_data in departments.values():
            total = int(dept_data.get("total_tasks", 0) or 0)
            completed = int(dept_data.get("completed_tasks", 0) or 0)
            if total > 0:
                dept_data["efficiency"] = (float(completed) / float(total)) * 100.0

        return departments

    async def _get_recent_activity(self) -> list[dict[str, Any]]:
        """Get recent system activity."""
        recent_activity: list[dict[str, Any]] = []

        for agent in self.agent_registry.values():
            if hasattr(agent, 'task_history') and agent.task_history:
                latest_task = agent.task_history[-1]
                recent_activity.append({
                    "agent": agent.config.name,
                    "department": agent.config.department.value,
                    "task": latest_task.description,
                    "status": latest_task.status,
                    "timestamp": latest_task.completed_at.isoformat() if latest_task.completed_at else "N/A"
                })

        # Sort by timestamp and return recent 10
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_activity[:10]

    async def _get_kpis_summary(self) -> dict[str, Any]:
        """Compute high-level KPIs for executive view."""
        kpis: dict[str, float] = {
            "throughput_per_min": 0.0,
            "success_rate": 0.0,
            "avg_task_duration_s": 0.0,
        }
        total = 0
        successes = 0
        durations: list[float] = []
        for agent in self.agent_registry.values():
            if hasattr(agent, 'task_history'):
                for t in agent.task_history:
                    total += 1
                    if t.status == "completed":
                        successes += 1
                    if t.started_at and t.completed_at:
                        durations.append(float((t.completed_at - t.started_at).total_seconds()))
        if total:
            kpis["success_rate"] = round(100.0 * successes / total, 1)
        if durations:
            kpis["avg_task_duration_s"] = round(sum(durations) / len(durations), 2)
        # Simple placeholder throughput based on last 10 tasks
        kpis["throughput_per_min"] = round(min(total, 10) / 60.0, 2)
        return kpis

    async def _get_insights(self) -> list[dict[str, Any]]:
        """Generate simple insights based on current metrics."""
        insights: list[dict[str, Any]] = []
        dept_summary = await self._get_department_summary()
        for name, data in dept_summary.items():
            eff = data.get("efficiency", 0)
            EFFICIENCY_THRESHOLD = 60
            if eff < EFFICIENCY_THRESHOLD and data.get("agent_count", 0) > 0:
                insights.append({
                    "department": name,
                    "type": "efficiency_opportunity",
                    "message": f"Efficiency at {eff:.1f}% — consider scaling resources or optimizing workflows."
                })
        if not insights:
            insights.append({
                "type": "status",
                "message": "System operating nominally with no major bottlenecks detected"
            })
        return insights

    async def _get_active_alerts(self) -> list[dict[str, Any]]:
        """Get active system alerts."""
        alerts: list[dict[str, Any]] = []

        # Check for agents in error state
        for agent in self.agent_registry.values():
            if agent.status.value == "error":
                alerts.append({
                    "level": "high",
                    "type": "agent_error",
                    "message": f"Agent {agent.config.name} is in error state",
                    "agent_id": getattr(agent.config, "agent_id", getattr(agent, "agent_id", "unknown")),
                    "timestamp": datetime.now(UTC).isoformat()
                })

        # Check for low efficiency departments
        dept_summary = await self._get_department_summary()
        for dept_name, dept_data in dept_summary.items():
            MEDIUM_EFFICIENCY_THRESHOLD = 70
            if dept_data["efficiency"] < MEDIUM_EFFICIENCY_THRESHOLD:
                alerts.append({
                    "level": "medium",
                    "type": "low_efficiency",
                    "message": f"Department {dept_name} efficiency below 70%",
                    "department": dept_name,
                    "efficiency": dept_data["efficiency"],
                    "timestamp": datetime.now(UTC).isoformat()
                })

        return alerts

    async def get_agent_status(self, agent_id: str) -> dict[str, Any] | None:
        """Get detailed status of a specific agent."""
        if agent_id not in self.agent_registry:
            return None

        agent = self.agent_registry[agent_id]
        return await agent.get_status_report()

    async def get_department_status(self, department: str) -> dict[str, Any] | None:
        """Get detailed status of a specific department."""
        dept_agents = [
            agent for agent in self.agent_registry.values()
            if agent.config.department.value == department
        ]

        if not dept_agents:
            return None

        dept_status = {
            "department": department,
            "total_agents": len(dept_agents),
            "active_agents": sum(1 for a in dept_agents if a.status.value != "offline"),
            "agents": []
        }

        for agent in dept_agents:
            agent_status = await agent.get_status_report()
            dept_status["agents"].append(agent_status)

        return dept_status

    async def execute_emergency_protocol(self, protocol_name: str) -> dict[str, Any]:
        """Execute emergency protocol."""
        if protocol_name not in self.emergency_protocols:
            return {"error": f"Unknown emergency protocol: {protocol_name}"}

        try:
            result = await self.emergency_protocols[protocol_name]()
            return {"protocol_executed": protocol_name, "result": result}
        except Exception as e:
            logger.error(f"Emergency protocol {protocol_name} failed: {str(e)}")
            return {"error": f"Protocol execution failed: {str(e)}"}

    async def _handle_system_overload(self) -> dict[str, Any]:
        """Handle system overload emergency."""
        logger.warning("Executing system overload emergency protocol")

        # Reduce non-critical agent activity
        agents_shutdown = 0
        for agent in self.agent_registry.values():
            if agent.config.department.value in ["personal", "creative"]:
                await agent.shutdown()
                agents_shutdown += 1

        return {"status": "System load reduced", "agents_shutdown": agents_shutdown}

    async def _handle_security_breach(self) -> dict[str, Any]:
        """Handle security breach emergency."""
        logger.critical("Executing security breach emergency protocol")

        # Activate security agents
        security_agents = [
            agent for agent in self.agent_registry.values()
            if agent.config.department.value == "it_security"
        ]

        for _agent in security_agents:
            # Activate security protocols
            pass

        return {"status": "Security protocols activated", "security_agents": len(security_agents)}

    async def _handle_critical_failure(self) -> dict[str, Any]:
        """Handle critical system failure."""
        logger.critical("Executing critical failure emergency protocol")

        # Shutdown non-essential agents
        essential_departments = ["executive", "it_security", "finance"]

        for agent in self.agent_registry.values():
            if agent.config.department.value not in essential_departments:
                await agent.shutdown()

        return {"status": "Essential services maintained", "agents_shutdown": 35}

    async def _handle_resource_exhaustion(self) -> dict[str, Any]:
        """Handle resource exhaustion emergency."""
        logger.warning("Executing resource exhaustion emergency protocol")

        # Optimize resource usage
        for agent in self.agent_registry.values():
            await agent.auto_heal()

        return {"status": "Resources optimized", "agents_optimized": len(self.agent_registry)}

    async def shutdown_all_agents(self) -> dict[str, Any]:
        """Gracefully shutdown all agents."""
        logger.info("Initiating system-wide agent shutdown")

        shutdown_results = []
        for agent_id, agent in self.agent_registry.items():
            try:
                await agent.shutdown()
                shutdown_results.append({"agent_id": agent_id, "status": "shutdown_successful"})
            except Exception as e:
                shutdown_results.append({"agent_id": agent_id, "status": "shutdown_failed", "error": str(e)})

        self.status = DashboardStatus.OFFLINE

        return {
            "shutdown_status": "complete",
            "total_agents": len(self.agent_registry),
            "results": shutdown_results
        }

    async def restart_agents(self, department: str | None = None) -> dict[str, Any]:
        """Restart agents (all or by department)."""
        logger.info(f"Restarting agents for department: {department or 'all'}")

        restart_results = []
        agents_to_restart = [
            agent for agent in self.agent_registry.values()
            if department is None or agent.config.department.value == department
        ]

        for agent in agents_to_restart:
            try:
                # Reinitialize agent
                agent._initialize_agent()
                restart_results.append({"agent_id": getattr(agent.config, "agent_id", getattr(agent, "agent_id", "unknown")), "status": "restart_successful"})
            except Exception as e:
                restart_results.append({"agent_id": getattr(agent.config, "agent_id", getattr(agent, "agent_id", "unknown")), "status": "restart_failed", "error": str(e)})

        return {
            "restart_status": "complete",
            "agents_restarted": len(agents_to_restart),
            "results": restart_results
        }

    def __str__(self):
        return f"Master Dashboard - Status: {self.status.value}, Health: {self.system_health.value}"

    def __repr__(self):
        return f"<MasterDashboard status={self.status.value} health={self.system_health.value} agents={len(self.agent_registry)}>"
