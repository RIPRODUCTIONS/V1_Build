from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgentDomain(str, Enum):
    RESEARCH = "research"
    MARKETING = "marketing"
    SALES = "sales"
    FINANCE = "finance"
    OPERATIONS = "operations"
    CONTENT = "content"
    ANALYTICS = "analytics"


class AgentCapability(str, Enum):
    # Research capabilities
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    TREND_MONITORING = "trend_monitoring"
    PRODUCT_RESEARCH = "product_research"

    # Marketing capabilities
    CAMPAIGN_GENERATION = "campaign_generation"
    SEO_OPTIMIZATION = "seo_optimization"
    CONTENT_CREATION = "content_creation"
    SOCIAL_MEDIA = "social_media"
    EMAIL_MARKETING = "email_marketing"

    # Sales capabilities
    LEAD_QUALIFICATION = "lead_qualification"
    OUTREACH_AUTOMATION = "outreach_automation"
    PIPELINE_MANAGEMENT = "pipeline_management"
    PROPOSAL_GENERATION = "proposal_generation"

    # Finance capabilities
    EXPENSE_TRACKING = "expense_tracking"
    INVOICE_PROCESSING = "invoice_processing"
    BUDGET_ANALYSIS = "budget_analysis"
    FINANCIAL_REPORTING = "financial_reporting"


@dataclass
class AgentConfig:
    agent_id: str
    name: str
    domain: AgentDomain
    capabilities: list[AgentCapability]
    priority: int = 5
    max_concurrent_tasks: int = 3
    retry_attempts: int = 3
    timeout_seconds: int = 300
    rate_limit_per_hour: int = 100
    external_apis: list[str] | None = None
    # ATOMIC shell tagging
    shell: str = "Q"
    energy_level: int = 7

    def __post_init__(self):
        if self.external_apis is None:
            self.external_apis = []


class AgentRegistry:
    def __init__(self):
        self.agents: dict[str, AgentConfig] = {}
        self.domain_agents: dict[AgentDomain, list[str]] = {domain: [] for domain in AgentDomain}

    def register_agent(self, config: AgentConfig) -> None:
        self.agents[config.agent_id] = config
        self.domain_agents[config.domain].append(config.agent_id)

    def get_agents_by_domain(self, domain: AgentDomain) -> list[AgentConfig]:
        return [self.agents[agent_id] for agent_id in self.domain_agents.get(domain, [])]

    def get_agents_by_capability(self, capability: AgentCapability) -> list[AgentConfig]:
        return [agent for agent in self.agents.values() if capability in agent.capabilities]


__all__ = [
    "AgentDomain",
    "AgentCapability",
    "AgentConfig",
    "AgentRegistry",
]


