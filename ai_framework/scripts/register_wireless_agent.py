
# Add this to your agent registration in main.py or server.py

from agents.cybersecurity import AISecurityMonitor

async def register_wireless_agent(agent_orchestrator):
    """Register AI security monitor agent."""
    # Register security monitor agent
    security_agent = AISecurityMonitor()
    await security_agent.initialize()
    agent_orchestrator.register_agent(security_agent)

    print("AI Security Monitor Agent registered successfully")

# Example usage:
# import asyncio
# from core.agent_orchestrator import AgentOrchestrator
# orchestrator = AgentOrchestrator()
# asyncio.run(register_wireless_agent(orchestrator))
