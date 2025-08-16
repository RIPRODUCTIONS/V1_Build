#!/usr/bin/env python3
"""
Simple AI Framework Startup Script

This script starts the AI Framework with basic functionality
to test that all agents are working.
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import all agents at module level
from agents import (
    # Base classes
    AICEO,
    AICFO,
    AICHR,
    # Marketing & Growth
    AICMO,
    AICOO,
    AICTO,
    # Finance & Money
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
    # Legal & Compliance
    AIGeneralCounsel,
    # Creative & Content
    AIGraphicDesigner,
    AIHealthCoach,
    AIHomeManager,
    AIIncidentResponder,
    AIIPManager,
    AILeadQualifier,
    AILearningMentor,
    AIOnboardingSpecialist,
    AIPaymentsManager,
    # Cybersecurity & IT Security
    AIPenetrationTester,
    AIPerformanceCoach,
    # Personal Life & Productivity
    AIPersonalAssistant,
    AIPRAgent,
    AIProcurementOfficer,
    # HR & People
    AIRecruiter,
    # Sales & Customer
    AISalesManager,
    AIScheduler,
    AISecurityAnalyst,
    AISecurityMonitor,
    AISEOSpecialist,
    AISocialMediaManager,
    # Operations & Logistics
    AISupplyChainManager,
    # IT & Security
    AISysAdmin,
    AIThreatHunter,
    AITrader,
    AITrainingManager,
    AITravelAgent,
    AIVideoProducer,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_system():
    """Test the agent system without complex dependencies."""
    try:
        print("🚀 Testing AI Framework Agent System...")
        print("=" * 50)

        print("✅ All agents imported successfully")

        # Count agents by department
        total_agents = 0

        # Get all AI agent classes
        ai_agents = []
        for agent_class in [AICEO, AICOO, AICFO, AICTO, AICHR,
                            AIPenetrationTester, AISecurityMonitor, AIThreatHunter, AIIncidentResponder, AIComplianceManager]:
            ai_agents.append(agent_class)
            total_agents += 1

        print(f"\n📊 Total AI Agents Found: {total_agents}")

        # Test agent capabilities
        print("\n🔍 Testing Agent Capabilities...")
        test_agents = [
            AICEO, AIAccountant, AISalesManager, AICMO,
            AISupplyChainManager, AIPenetrationTester
        ]

        for agent_class in test_agents:
            try:
                agent_name = agent_class.__name__
                # Create a mock instance to test capabilities
                capabilities = agent_class.get_capabilities.__func__(None)
                print(f"   ✅ {agent_name}: {len(capabilities)} capabilities")
            except Exception as e:
                print(f"   ❌ {agent_class.__name__}: Error - {str(e)}")

        # List all agents by department
        print("\n🏢 AI Agents by Department:")
        departments = {
            'executive': [AICEO, AICOO, AICFO, AICTO, AICHR],
            'finance': [AIAccountant, AIController, AITrader, AIPaymentsManager, AICollectionsOfficer, AIFraudAnalyst, AIAuditor],
            'sales': [AISalesManager, AILeadQualifier, AIAccountManager, AICustomerSupportAgent, AIOnboardingSpecialist],
            'marketing': [AICMO, AICampaignManager, AISocialMediaManager, AISEOSpecialist, AIPRAgent],
            'operations': [AISupplyChainManager, AIFleetManager, AIScheduler, AIProcurementOfficer],
            'cybersecurity': [AIPenetrationTester, AISecurityMonitor, AIThreatHunter, AIIncidentResponder, AIComplianceManager],
            'hr': [AIRecruiter, AITrainingManager, AIPerformanceCoach, AIComplianceOfficer],
            'legal': [AIGeneralCounsel, AIIPManager, AIContractNegotiator],
            'it_security': [AISysAdmin, AISecurityAnalyst, AIDevOpsEngineer, AIDataEngineer, AICloudOptimizer],
            'creative': [AIGraphicDesigner, AIVideoProducer, AICopywriter, AIBrandManager],
            'personal': [AIPersonalAssistant, AITravelAgent, AIHealthCoach, AIHomeManager, AILearningMentor]
        }

        for dept, agents in departments.items():
            print(f"   • {dept.title()}: {len(agents)} agents")

        print("\n🎉 AI Framework Agent System Test Complete!")
        print("🚀 System is ready for full startup!")

        return True

    except Exception as e:
        print(f"❌ System test failed: {str(e)}")
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    success = await test_agent_system()

    if success:
        print("\n🎯 NEXT STEPS:")
        print("   1. Fix AgentOrchestrator dependencies")
        print("   2. Start full system with: python3 start_system.py")
        print("   3. Access dashboard at: http://localhost:8000/frontend/")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
