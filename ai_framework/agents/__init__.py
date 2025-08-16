"""
AI Framework Agents Module

This module contains all specialized AI agents organized by department/domain:
- Executive & Strategy Agents
- Finance & Money Agents
- Sales & Customer Agents
- Marketing & Growth Agents
- Operations & Logistics Agents
- Cybersecurity & IT Security Agents
- HR & People Agents
- Legal & Compliance Agents
- IT & Security Agents
- Creative & Content Agents
- Personal Life & Productivity Agents

Each agent is autonomous, works together with others, and is visible in the master control dashboard.
"""

from .base import AgentStatus, AgentType, BaseAgent, TaskPriority
from .creative import AIBrandManager, AICopywriter, AIGraphicDesigner, AIVideoProducer
from .cybersecurity import (
    AIComplianceManager,
    AIIncidentResponder,
    AIPenetrationTester,
    AISecurityMonitor,
    AIThreatHunter,
)
from .executive import AICEO, AICFO, AICHR, AICOO, AICTO
from .finance import (
    AIAccountant,
    AIAuditor,
    AICollectionsOfficer,
    AIController,
    AIFraudAnalyst,
    AIPaymentsManager,
    AITrader,
)
from .hr import AIComplianceOfficer, AIPerformanceCoach, AIRecruiter, AITrainingManager
from .it_security import (
    AICloudOptimizer,
    AIDataEngineer,
    AIDevOpsEngineer,
    AISecurityAnalyst,
    AISysAdmin,
)
from .legal import AIContractNegotiator, AIGeneralCounsel, AIIPManager
from .marketing import AICMO, AICampaignManager, AIPRAgent, AISEOSpecialist, AISocialMediaManager
from .operations import AIFleetManager, AIProcurementOfficer, AIScheduler, AISupplyChainManager
from .personal import (
    AIHealthCoach,
    AIHomeManager,
    AILearningMentor,
    AIPersonalAssistant,
    AITravelAgent,
)
from .sales import (
    AIAccountManager,
    AICustomerSupportAgent,
    AILeadQualifier,
    AIOnboardingSpecialist,
    AISalesManager,
)

__all__ = [
    # Base classes
    "BaseAgent", "AgentType", "AgentStatus", "TaskPriority",

    # Executive & Strategy
    "AICEO", "AICOO", "AICFO", "AICTO", "AICHR",

    # Finance & Money
    "AIAccountant", "AIController", "AITrader", "AIPaymentsManager",
    "AICollectionsOfficer", "AIFraudAnalyst", "AIAuditor",

    # Sales & Customer
    "AISalesManager", "AILeadQualifier", "AIAccountManager",
    "AICustomerSupportAgent", "AIOnboardingSpecialist",

    # Marketing & Growth
    "AICMO", "AICampaignManager", "AISocialMediaManager",
    "AISEOSpecialist", "AIPRAgent",

    # Operations & Logistics
    "AISupplyChainManager", "AIFleetManager", "AIScheduler", "AIProcurementOfficer",

    # Cybersecurity & IT Security
    "AIPenetrationTester", "AISecurityMonitor", "AIThreatHunter",
    "AIIncidentResponder", "AIComplianceManager",

    # HR & People
    "AIRecruiter", "AITrainingManager", "AIPerformanceCoach", "AIComplianceOfficer",

    # Legal & Compliance
    "AIGeneralCounsel", "AIIPManager", "AIContractNegotiator",

    # IT & Security
    "AISysAdmin", "AISecurityAnalyst", "AIDevOpsEngineer",
    "AIDataEngineer", "AICloudOptimizer",

    # Creative & Content
    "AIGraphicDesigner", "AIVideoProducer", "AICopywriter", "AIBrandManager",

    # Personal Life & Productivity
    "AIPersonalAssistant", "AITravelAgent", "AIHealthCoach",
    "AIHomeManager", "AILearningMentor"
]
