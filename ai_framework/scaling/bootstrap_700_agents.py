from __future__ import annotations

from .agent_registry import AgentCapability, AgentConfig, AgentDomain, AgentRegistry


def bootstrap_700_agents() -> AgentRegistry:
    registry = AgentRegistry()

    # Shell mapping helpers
    def tag(cfg: AgentConfig, shell: str, level: int) -> AgentConfig:
        cfg.shell = shell
        cfg.energy_level = level
        return cfg

    research_agents = [
        *[
            tag(AgentConfig(
                agent_id=f"market_research_{i:03d}",
                name=f"Market Research Agent {i}",
                domain=AgentDomain.RESEARCH,
                capabilities=[AgentCapability.MARKET_RESEARCH, AgentCapability.TREND_MONITORING],
                priority=8,
                max_concurrent_tasks=2,
                rate_limit_per_hour=50,
            ), "N", 4)
            for i in range(1, 26)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"competitor_analysis_{i:03d}",
                name=f"Competitor Analysis Agent {i}",
                domain=AgentDomain.RESEARCH,
                capabilities=[AgentCapability.COMPETITOR_ANALYSIS, AgentCapability.MARKET_RESEARCH],
                priority=7,
                max_concurrent_tasks=3,
                rate_limit_per_hour=75,
            ), "N", 4)
            for i in range(1, 26)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"product_research_{i:03d}",
                name=f"Product Research Agent {i}",
                domain=AgentDomain.RESEARCH,
                capabilities=[AgentCapability.PRODUCT_RESEARCH, AgentCapability.TREND_MONITORING],
                priority=8,
                max_concurrent_tasks=2,
                rate_limit_per_hour=60,
            ), "N", 4)
            for i in range(1, 26)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"trend_monitor_{i:03d}",
                name=f"Trend Monitoring Agent {i}",
                domain=AgentDomain.RESEARCH,
                capabilities=[AgentCapability.TREND_MONITORING],
                priority=6,
                max_concurrent_tasks=4,
                rate_limit_per_hour=100,
            ), "N", 4)
            for i in range(1, 26)
        ],
    ]

    marketing_agents = [
        *[
            tag(AgentConfig(
                agent_id=f"content_creator_{i:03d}",
                name=f"Content Creator Agent {i}",
                domain=AgentDomain.MARKETING,
                capabilities=[AgentCapability.CONTENT_CREATION, AgentCapability.SEO_OPTIMIZATION],
                priority=7,
                max_concurrent_tasks=3,
                rate_limit_per_hour=80,
            ), "P", 6)
            for i in range(1, 51)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"seo_optimizer_{i:03d}",
                name=f"SEO Optimizer Agent {i}",
                domain=AgentDomain.MARKETING,
                capabilities=[AgentCapability.SEO_OPTIMIZATION, AgentCapability.CONTENT_CREATION],
                priority=8,
                max_concurrent_tasks=2,
                rate_limit_per_hour=60,
            ), "O", 5)
            for i in range(1, 41)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"campaign_gen_{i:03d}",
                name=f"Campaign Generator Agent {i}",
                domain=AgentDomain.MARKETING,
                capabilities=[AgentCapability.CAMPAIGN_GENERATION, AgentCapability.CONTENT_CREATION],
                priority=9,
                max_concurrent_tasks=2,
                rate_limit_per_hour=50,
            ), "M", 3)
            for i in range(1, 41)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"social_media_{i:03d}",
                name=f"Social Media Agent {i}",
                domain=AgentDomain.MARKETING,
                capabilities=[AgentCapability.SOCIAL_MEDIA, AgentCapability.CONTENT_CREATION],
                priority=7,
                max_concurrent_tasks=4,
                rate_limit_per_hour=120,
            ), "P", 6)
            for i in range(1, 36)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"email_marketing_{i:03d}",
                name=f"Email Marketing Agent {i}",
                domain=AgentDomain.MARKETING,
                capabilities=[AgentCapability.EMAIL_MARKETING, AgentCapability.CONTENT_CREATION],
                priority=8,
                max_concurrent_tasks=3,
                rate_limit_per_hour=90,
            ), "P", 6)
            for i in range(1, 36)
        ],
    ]

    sales_agents = [
        *[
            tag(AgentConfig(
                agent_id=f"lead_qualifier_{i:03d}",
                name=f"Lead Qualifier Agent {i}",
                domain=AgentDomain.SALES,
                capabilities=[AgentCapability.LEAD_QUALIFICATION, AgentCapability.PIPELINE_MANAGEMENT],
                priority=9,
                max_concurrent_tasks=5,
                rate_limit_per_hour=150,
                external_apis=["crm", "lead_enrichment"],
            ), "N", 4)
            for i in range(1, 71)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"outreach_auto_{i:03d}",
                name=f"Outreach Automation Agent {i}",
                domain=AgentDomain.SALES,
                capabilities=[AgentCapability.OUTREACH_AUTOMATION, AgentCapability.LEAD_QUALIFICATION],
                priority=8,
                max_concurrent_tasks=3,
                rate_limit_per_hour=100,
                external_apis=["email", "crm", "linkedin"],
            ), "P", 6)
            for i in range(1, 71)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"pipeline_mgr_{i:03d}",
                name=f"Pipeline Manager Agent {i}",
                domain=AgentDomain.SALES,
                capabilities=[AgentCapability.PIPELINE_MANAGEMENT],
                priority=7,
                max_concurrent_tasks=4,
                rate_limit_per_hour=80,
                external_apis=["crm"],
            ), "O", 5)
            for i in range(1, 31)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"proposal_gen_{i:03d}",
                name=f"Proposal Generator Agent {i}",
                domain=AgentDomain.SALES,
                capabilities=[AgentCapability.PROPOSAL_GENERATION],
                priority=8,
                max_concurrent_tasks=2,
                rate_limit_per_hour=40,
                external_apis=["document_gen", "crm"],
            ), "O", 5)
            for i in range(1, 31)
        ],
    ]

    finance_agents = [
        *[
            tag(AgentConfig(
                agent_id=f"expense_tracker_{i:03d}",
                name=f"Expense Tracker Agent {i}",
                domain=AgentDomain.FINANCE,
                capabilities=[AgentCapability.EXPENSE_TRACKING],
                priority=6,
                max_concurrent_tasks=5,
                rate_limit_per_hour=200,
                external_apis=["banking", "expense_mgmt"],
            ), "P", 6)
            for i in range(1, 31)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"invoice_processor_{i:03d}",
                name=f"Invoice Processor Agent {i}",
                domain=AgentDomain.FINANCE,
                capabilities=[AgentCapability.INVOICE_PROCESSING],
                priority=8,
                max_concurrent_tasks=3,
                rate_limit_per_hour=100,
                external_apis=["accounting", "ocr"],
            ), "O", 5)
            for i in range(1, 26)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"budget_analyzer_{i:03d}",
                name=f"Budget Analyzer Agent {i}",
                domain=AgentDomain.FINANCE,
                capabilities=[AgentCapability.BUDGET_ANALYSIS],
                priority=7,
                max_concurrent_tasks=2,
                rate_limit_per_hour=60,
                external_apis=["accounting", "forecasting"],
            ), "O", 5)
            for i in range(1, 26)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"financial_reporter_{i:03d}",
                name=f"Financial Reporter Agent {i}",
                domain=AgentDomain.FINANCE,
                capabilities=[AgentCapability.FINANCIAL_REPORTING],
                priority=9,
                max_concurrent_tasks=1,
                rate_limit_per_hour=30,
                external_apis=["accounting", "analytics"],
            ), "M", 3)
            for i in range(1, 21)
        ],
    ]

    operations_agents = [
        *[
            tag(AgentConfig(
                agent_id=f"operations_{i:03d}",
                name=f"Operations Agent {i}",
                domain=AgentDomain.OPERATIONS,
                capabilities=[AgentCapability.EXPENSE_TRACKING],
                priority=5,
                max_concurrent_tasks=3,
                rate_limit_per_hour=120,
            ), "P", 6)
            for i in range(1, 51)
        ],
        *[
            tag(AgentConfig(
                agent_id=f"analytics_{i:03d}",
                name=f"Analytics Agent {i}",
                domain=AgentDomain.ANALYTICS,
                capabilities=[AgentCapability.FINANCIAL_REPORTING],
                priority=6,
                max_concurrent_tasks=4,
                rate_limit_per_hour=100,
            ), "O", 5)
            for i in range(1, 51)
        ],
    ]

    all_agents = research_agents + marketing_agents + sales_agents + finance_agents + operations_agents
    for agent in all_agents:
        registry.register_agent(agent)

    return registry


__all__ = ["bootstrap_700_agents"]


