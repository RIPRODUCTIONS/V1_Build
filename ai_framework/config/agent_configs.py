#!/usr/bin/env python3
"""
Agent Configuration System

This module provides stable, reliable configurations for all AI agents
in the framework. No patches or shortcuts - proper configurations.
"""

from agents.base import AgentConfig, AgentDepartment, AgentType


def _cfg(name: str, agent_type: AgentType, department: AgentDepartment, capabilities: list[str], **kwargs) -> AgentConfig:
    return AgentConfig(
        name=name,
        agent_type=agent_type,
        department=department,
        capabilities=capabilities,
        max_concurrent_tasks=kwargs.get("max_concurrent_tasks", 3),
        collaboration_enabled=kwargs.get("collaboration_enabled", True),
        auto_heal_enabled=kwargs.get("auto_heal_enabled", True),
        heartbeat_interval=kwargs.get("heartbeat_interval", 30),
        max_memory_gb=kwargs.get("max_memory_gb", 6.0),
        cost_per_hour=kwargs.get("cost_per_hour", 20.0),
        priority_level=kwargs.get("priority_level", 1)
    )

def get_executive_agent_configs() -> dict[str, AgentConfig]:
    """Get configurations for Executive & Strategy agents."""
    return {
        "ai_ceo": AgentConfig(
            name="AI CEO",
            agent_type=AgentType.CEO,
            department=AgentDepartment.EXECUTIVE,
            capabilities=[
                "strategic_planning",
                "kpi_analysis",
                "resource_allocation",
                "risk_assessment",
                "board_communication",
                "stakeholder_management",
                "market_analysis",
                "competitive_intelligence",
                "merger_acquisition_strategy",
                "crisis_management"
            ],
            max_concurrent_tasks=3,
            cost_per_hour=25.0,
            max_memory_gb=8.0,
            priority_level=1
        ),

        "ai_coo": AgentConfig(
            name="AI COO",
            agent_type=AgentType.COO,
            department=AgentDepartment.EXECUTIVE,
            capabilities=[
                "operations_management",
                "process_optimization",
                "performance_monitoring",
                "resource_allocation",
                "team_coordination",
                "efficiency_analysis",
                "quality_management",
                "supply_chain_oversight"
            ],
            max_concurrent_tasks=5,
            cost_per_hour=20.0,
            max_memory_gb=6.0,
            priority_level=2
        ),

        "ai_cfo": AgentConfig(
            name="AI CFO",
            agent_type=AgentType.CFO,
            department=AgentDepartment.EXECUTIVE,
            capabilities=[
                "financial_planning",
                "budget_management",
                "investment_analysis",
                "cost_optimization",
                "financial_reporting",
                "risk_assessment",
                "compliance_monitoring",
                "cash_flow_management"
            ],
            max_concurrent_tasks=4,
            cost_per_hour=20.0,
            max_memory_gb=6.0,
            priority_level=2
        ),

        "ai_cto": AgentConfig(
            name="AI CTO",
            agent_type=AgentType.CTO,
            department=AgentDepartment.EXECUTIVE,
            capabilities=[
                "technology_strategy",
                "architecture_planning",
                "innovation_management",
                "digital_transformation",
                "cybersecurity_strategy",
                "data_strategy",
                "cloud_strategy",
                "vendor_management"
            ],
            max_concurrent_tasks=4,
            cost_per_hour=20.0,
            max_memory_gb=6.0,
            priority_level=2
        ),

        "ai_chro": AgentConfig(
            name="AI CHRO",
            agent_type=AgentType.CHRO,
            department=AgentDepartment.EXECUTIVE,
            capabilities=[
                "talent_strategy",
                "culture_development",
                "organizational_design",
                "change_management",
                "employee_engagement",
                "diversity_inclusion",
                "performance_management",
                "learning_development"
            ],
            max_concurrent_tasks=4,
            cost_per_hour=18.0,
            max_memory_gb=5.0,
            priority_level=2
        )
    }

def get_cybersecurity_agent_configs() -> dict[str, AgentConfig]:
    """Get configurations for Cybersecurity & IT Security agents."""
    return {
        "ai_penetration_tester": AgentConfig(
            name="AI Penetration Tester",
            agent_type=AgentType.SECURITY_ANALYST,
            department=AgentDepartment.CYBERSECURITY,
            capabilities=[
                "network_scanning",
                "vulnerability_assessment",
                "web_application_testing",
                "social_engineering_assessment",
                "security_reporting",
                "Kali_tool_integration",
                "penetration_testing",
                "security_auditing"
            ],
            max_concurrent_tasks=2,
            cost_per_hour=30.0,
            max_memory_gb=12.0,
            priority_level=1
        ),

        "ai_security_monitor": AgentConfig(
            name="AI Security Monitor",
            agent_type=AgentType.SECURITY_ANALYST,
            department=AgentDepartment.CYBERSECURITY,
            capabilities=[
                "threat_detection",
                "incident_response",
                "security_log_analysis",
                "alert_management",
                "real_time_monitoring",
                "threat_intelligence_integration",
                "security_metrics",
                "compliance_monitoring"
            ],
            max_concurrent_tasks=3,
            cost_per_hour=25.0,
            max_memory_gb=10.0,
            priority_level=2
        ),

        "ai_threat_hunter": AgentConfig(
            name="AI Threat Hunter",
            agent_type=AgentType.SECURITY_ANALYST,
            department=AgentDepartment.CYBERSECURITY,
            capabilities=[
                "threat_hunting",
                "indicator_analysis",
                "threat_intelligence_gathering",
                "advanced_persistent_threat_detection",
                "malware_analysis",
                "forensic_investigation",
                "threat_modeling",
                "intelligence_sharing"
            ],
            max_concurrent_tasks=2,
            cost_per_hour=35.0,
            max_memory_gb=16.0,
            priority_level=1
        ),

        "ai_incident_responder": AgentConfig(
            name="AI Incident Responder",
            agent_type=AgentType.SECURITY_ANALYST,
            department=AgentDepartment.CYBERSECURITY,
            capabilities=[
                "incident_coordination",
                "evidence_collection",
                "communication_management",
                "response_playbook_execution",
                "stakeholder_coordination",
                "recovery_planning",
                "lessons_learned_analysis",
                "post_incident_review"
            ],
            max_concurrent_tasks=2,
            cost_per_hour=30.0,
            max_memory_gb=12.0,
            priority_level=2
        ),

        "ai_compliance_manager": AgentConfig(
            name="AI Compliance Manager",
            agent_type=AgentType.COMPLIANCE_OFFICER,
            department=AgentDepartment.CYBERSECURITY,
            capabilities=[
                "compliance_assessment",
                "audit_preparation",
                "policy_management",
                "regulatory_monitoring",
                "risk_assessment",
                "compliance_reporting",
                "training_coordination",
                "gap_analysis"
            ],
            max_concurrent_tasks=3,
            cost_per_hour=20.0,
            max_memory_gb=8.0,
            priority_level=2
        )
    }

def get_finance_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_accountant": _cfg("AI Accountant", AgentType.ACCOUNTANT, AgentDepartment.FINANCE,
                               ["bookkeeping", "tax_preparation", "compliance_check", "financial_reconciliation"]),
        "ai_controller": _cfg("AI Controller", AgentType.CONTROLLER, AgentDepartment.FINANCE,
                               ["financial_controls", "budget_management", "variance_analysis", "reporting"]),
        "ai_trader": _cfg("AI Trader", AgentType.TRADER, AgentDepartment.FINANCE,
                           ["market_analysis", "trade_execution", "risk_management", "portfolio_optimization"], max_concurrent_tasks=900),
        "ai_payments_manager": _cfg("AI Payments Manager", AgentType.PAYMENTS_MANAGER, AgentDepartment.FINANCE,
                                     ["ap_processing", "ar_management", "cash_flow", "reconciliation"]),
        "ai_collections_officer": _cfg("AI Collections Officer", AgentType.COLLECTIONS_OFFICER, AgentDepartment.FINANCE,
                                        ["collections", "dunning", "payment_plans", "risk_scoring"]),
        "ai_fraud_analyst": _cfg("AI Fraud Analyst", AgentType.FRAUD_ANALYST, AgentDepartment.FINANCE,
                                  ["fraud_detection", "pattern_analysis", "investigation", "account_monitoring"], max_concurrent_tasks=900),
        "ai_auditor": _cfg("AI Auditor", AgentType.AUDITOR, AgentDepartment.FINANCE,
                             ["compliance_audit", "efficiency_audit", "risk_assessment", "internal_controls"]),
    }

def get_sales_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_sales_manager": _cfg("AI Sales Manager", AgentType.SALES_MANAGER, AgentDepartment.SALES,
                                  ["lead_assignment", "quota_tracking", "script_optimization", "sales_forecasting"]),
        "ai_lead_qualifier": _cfg("AI Lead Qualifier", AgentType.LEAD_QUALIFIER, AgentDepartment.SALES,
                                   ["lead_scoring", "qualification", "criteria_update", "handoff"]),
        "ai_account_manager": _cfg("AI Account Manager", AgentType.ACCOUNT_MANAGER, AgentDepartment.SALES,
                                    ["customer_checkin", "upsell_opportunity", "renewal_management", "relationship_building"]),
        "ai_customer_support": _cfg("AI Customer Support", AgentType.CUSTOMER_SUPPORT, AgentDepartment.SALES,
                                     ["ticket_resolution", "escalation_handling", "knowledge_base_update", "sla_management"]),
        "ai_onboarding_specialist": _cfg("AI Onboarding Specialist", AgentType.ONBOARDING_SPECIALIST, AgentDepartment.SALES,
                                          ["onboarding_playbooks", "training_scheduling", "progress_tracking", "customer_success"]),
    }

def get_marketing_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_cmo": _cfg("AI CMO", AgentType.CMO, AgentDepartment.MARKETING,
                        ["strategy_development", "budget_allocation", "channel_selection", "performance_analysis"]),
        "ai_campaign_manager": _cfg("AI Campaign Manager", AgentType.CAMPAIGN_MANAGER, AgentDepartment.MARKETING,
                                     ["campaign_planning", "execution", "optimization", "reporting"]),
        "ai_social_media_manager": _cfg("AI Social Media Manager", AgentType.SOCIAL_MEDIA_MANAGER, AgentDepartment.MARKETING,
                                         ["content_calendar", "community_management", "social_performance", "brand_listening"]),
        "ai_seo_specialist": _cfg("AI SEO Specialist", AgentType.SEO_SPECIALIST, AgentDepartment.MARKETING,
                                   ["keyword_research", "content_optimization", "rankings_analysis", "technical_seo"]),
        "ai_pr_agent": _cfg("AI PR Agent", AgentType.PR_AGENT, AgentDepartment.MARKETING,
                             ["media_outreach", "press_releases", "crisis_management", "reputation"]),
    }

def get_operations_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_supply_chain_manager": _cfg("AI Supply Chain Manager", AgentType.SUPPLY_CHAIN_MANAGER, AgentDepartment.OPERATIONS,
                                         ["demand_forecasting", "inventory_optimization", "supplier_management", "logistics_planning"]),
        "ai_fleet_manager": _cfg("AI Fleet Manager", AgentType.FLEET_MANAGER, AgentDepartment.OPERATIONS,
                                  ["route_optimization", "maintenance_scheduling", "fleet_performance", "compliance"]),
        "ai_scheduler": _cfg("AI Scheduler", AgentType.SCHEDULER, AgentDepartment.OPERATIONS,
                              ["shift_planning", "workload_balancing", "calendar_optimization", "resource_allocation"]),
        "ai_procurement_officer": _cfg("AI Procurement Officer", AgentType.PROCUREMENT_OFFICER, AgentDepartment.OPERATIONS,
                                        ["supplier_sourcing", "rfq_management", "contract_negotiation", "cost_optimization"]),
    }

def get_hr_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_recruiter": _cfg("AI Recruiter", AgentType.RECRUITER, AgentDepartment.HR,
                               ["job_postings", "candidate_screening", "interview_scheduling", "offer_management"]),
        "ai_training_manager": _cfg("AI Training Manager", AgentType.TRAINING_MANAGER, AgentDepartment.HR,
                                     ["training_needs", "curriculum_design", "learning_paths", "upskilling"]),
        "ai_performance_coach": _cfg("AI Performance Coach", AgentType.PERFORMANCE_COACH, AgentDepartment.HR,
                                      ["goal_setting", "feedback_cycles", "performance_reviews", "career_growth"]),
        "ai_compliance_officer": _cfg("AI Compliance Officer", AgentType.COMPLIANCE_OFFICER, AgentDepartment.HR,
                                       ["policy_management", "compliance_training", "incident_tracking", "audit_support"]),
    }

def get_legal_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_general_counsel": _cfg("AI General Counsel", AgentType.GENERAL_COUNSEL, AgentDepartment.LEGAL,
                                    ["legal_advice", "risk_management", "policy_review", "governance"]),
        "ai_ip_manager": _cfg("AI IP Manager", AgentType.IP_MANAGER, AgentDepartment.LEGAL,
                               ["patent_filing", "trademark_monitoring", "ip_portfolio", "licensing"]),
        "ai_contract_negotiator": _cfg("AI Contract Negotiator", AgentType.CONTRACT_NEGOTIATOR, AgentDepartment.LEGAL,
                                        ["contract_drafting", "redlining", "negotiation", "approval_workflow"]),
    }

def get_it_security_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_sysadmin": _cfg("AI SysAdmin", AgentType.SYSADMIN, AgentDepartment.IT_SECURITY,
                             ["provisioning", "monitoring", "backup_recovery", "patch_management"]),
        "ai_security_analyst": _cfg("AI Security Analyst", AgentType.SECURITY_ANALYST, AgentDepartment.IT_SECURITY,
                                     ["siem_monitoring", "alert_triage", "incident_response", "threat_hunting"]),
        "ai_devops_engineer": _cfg("AI DevOps Engineer", AgentType.DEVOPS_ENGINEER, AgentDepartment.IT_SECURITY,
                                    ["ci_cd", "infrastructure_as_code", "observability", "cost_optimization"]),
        "ai_data_engineer": _cfg("AI Data Engineer", AgentType.DATA_ENGINEER, AgentDepartment.IT_SECURITY,
                                  ["pipelines", "etl", "data_quality", "governance"]),
        "ai_cloud_optimizer": _cfg("AI Cloud Optimizer", AgentType.CLOUD_OPTIMIZER, AgentDepartment.IT_SECURITY,
                                   ["rightsizing", "performance_tuning", "security_hardening", "cost_reports"]),
    }

def get_creative_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_graphic_designer": _cfg("AI Graphic Designer", AgentType.GRAPHIC_DESIGNER, AgentDepartment.CREATIVE,
                                     ["branding", "illustration", "ui_design", "ads_creatives"]),
        "ai_video_producer": _cfg("AI Video Producer", AgentType.VIDEO_PRODUCER, AgentDepartment.CREATIVE,
                                   ["storyboards", "editing", "motion_graphics", "publishing"]),
        "ai_copywriter": _cfg("AI Copywriter", AgentType.COPYWRITER, AgentDepartment.CREATIVE,
                               ["long_form", "ad_copy", "web_copy", "seo_copy"]),
        "ai_brand_manager": _cfg("AI Brand Manager", AgentType.BRAND_MANAGER, AgentDepartment.CREATIVE,
                                  ["brand_guidelines", "voice_tone", "campaign_alignment", "asset_library"]),
    }

def get_personal_agent_configs() -> dict[str, AgentConfig]:
    return {
        "ai_personal_assistant": _cfg("AI Personal Assistant", AgentType.PERSONAL_ASSISTANT, AgentDepartment.PERSONAL,
                                       ["calendar", "email", "tasks", "reminders"]),
        "ai_travel_agent": _cfg("AI Travel Agent", AgentType.TRAVEL_AGENT, AgentDepartment.PERSONAL,
                                 ["itineraries", "bookings", "deals", "visa_requirements"]),
        "ai_health_coach": _cfg("AI Health Coach", AgentType.HEALTH_COACH, AgentDepartment.PERSONAL,
                                 ["habits", "fitness", "nutrition", "tracking"]),
        "ai_home_manager": _cfg("AI Home Manager", AgentType.HOME_MANAGER, AgentDepartment.PERSONAL,
                                 ["maintenance", "inventory", "automation", "bills"]),
        "ai_learning_mentor": _cfg("AI Learning Mentor", AgentType.LEARNING_MENTOR, AgentDepartment.PERSONAL,
                                    ["curriculum", "practice", "assessment", "progress_tracking"]),
    }

def get_all_agent_configs() -> dict[str, AgentConfig]:
    """Get configurations for all agents in the system."""
    configs = {}

    # Add executive agents
    configs.update(get_executive_agent_configs())

    # Add cybersecurity agents
    configs.update(get_cybersecurity_agent_configs())
    # Add remaining departments
    configs.update(get_finance_agent_configs())
    configs.update(get_sales_agent_configs())
    configs.update(get_marketing_agent_configs())
    configs.update(get_operations_agent_configs())
    configs.update(get_hr_agent_configs())
    configs.update(get_legal_agent_configs())
    configs.update(get_it_security_agent_configs())
    configs.update(get_creative_agent_configs())
    configs.update(get_personal_agent_configs())

    return configs

def get_agent_config(agent_name: str) -> AgentConfig:
    """Get configuration for a specific agent."""
    configs = get_all_agent_configs()
    return configs.get(agent_name)

def validate_agent_configs() -> bool:
    """Validate all agent configurations."""
    try:
        configs = get_all_agent_configs()
        for _name, config in configs.items():
            # This will trigger __post_init__ validation
            AgentConfig(
                name=config.name,
                agent_type=config.agent_type,
                department=config.department,
                capabilities=config.capabilities,
                max_concurrent_tasks=config.max_concurrent_tasks,
                collaboration_enabled=config.collaboration_enabled,
                auto_heal_enabled=config.auto_heal_enabled,
                heartbeat_interval=config.heartbeat_interval,
                max_memory_gb=config.max_memory_gb,
                cost_per_hour=config.cost_per_hour,
                priority_level=config.priority_level
            )
        return True
    except Exception as e:
        print(f"Configuration validation failed: {str(e)}")
        return False
