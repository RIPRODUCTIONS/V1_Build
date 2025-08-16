"""
Master Agent Ecosystem Orchestrator
Manages all AI agents, their interactions, and the overall system intelligence
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from autonomous_system.agents.base_agent import AgentPriority, BaseAgent


class MasterOrchestrator:
    """Master orchestrator for the entire AI agent ecosystem"""

    def __init__(self):
        self.logger = logging.getLogger("master_orchestrator")

        # Agent registry
        self.agents: dict[str, BaseAgent] = {}
        self.agent_metadata: dict[str, dict[str, Any]] = {}

        # Agent relationships and dependencies
        self.agent_dependencies: dict[str, set[str]] = {}
        self.collaboration_networks: dict[str, set[str]] = {}
        self.workflow_chains: dict[str, list[str]] = {}

        # System intelligence
        self.system_knowledge: dict[str, Any] = {}
        self.decision_history: list[dict[str, Any]] = []
        self.performance_metrics: dict[str, Any] = {}

        # Task management
        self.task_queue: list[dict[str, Any]] = []
        self.active_tasks: dict[str, dict[str, Any]] = {}
        self.completed_tasks: list[dict[str, Any]] = []

        # Communication and messaging
        self.message_bus: dict[str, list[dict[str, Any]]] = {}
        self.broadcast_channels: set[str] = set()

        # Monitoring and health
        self.system_health: dict[str, Any] = {}
        self.agent_health: dict[str, dict[str, Any]] = {}

        # Learning and optimization
        self.learning_data: list[dict[str, Any]] = []
        self.optimization_history: list[dict[str, Any]] = []

        self.logger.info("Master Agent Ecosystem Orchestrator initialized")

        # Start background tasks
        asyncio.create_task(self._system_monitoring())
        asyncio.create_task(self._task_processing())
        asyncio.create_task(self._learning_cycle())
        asyncio.create_task(self._optimization_cycle())

    async def register_agent(self, agent: BaseAgent):
        """Register a new agent in the ecosystem"""
        try:
            agent_id = agent.agent_id

            # Register agent
            self.agents[agent_id] = agent
            self.agent_metadata[agent_id] = {
                "name": agent.name,
                "description": agent.description,
                "capabilities": [cap.value for cap in agent.capabilities],
                "priority": agent.priority.value,
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }

            # Initialize agent health monitoring
            self.agent_health[agent_id] = {
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "performance_score": 1.0,
                "error_count": 0
            }

            # Initialize message bus for agent
            self.message_bus[agent_id] = []

            # Analyze agent dependencies
            await self._analyze_agent_dependencies(agent_id)

            # Update collaboration networks
            await self._update_collaboration_networks(agent_id)

            self.logger.info(f"Agent registered: {agent.name} ({agent_id})")

        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            raise

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the ecosystem"""
        try:
            if agent_id in self.agents:
                agent_name = self.agents[agent_id].name

                # Remove agent from all registries
                del self.agents[agent_id]
                del self.agent_metadata[agent_id]
                del self.agent_health[agent_id]

                # Clean up dependencies
                await self._cleanup_agent_dependencies(agent_id)

                # Clean up collaboration networks
                await self._cleanup_collaboration_networks(agent_id)

                # Clean up message bus
                if agent_id in self.message_bus:
                    del self.message_bus[agent_id]

                self.logger.info(f"Agent unregistered: {agent_name} ({agent_id})")
            else:
                self.logger.warning(f"Agent not found for unregistration: {agent_id}")

        except Exception as e:
            self.logger.error(f"Failed to unregister agent: {e}")

    async def execute_task(self, task_data: dict[str, Any],
                          target_agent: str | None = None,
                          priority: AgentPriority = AgentPriority.MEDIUM) -> dict[str, Any]:
        """Execute a task using the most appropriate agent(s)"""
        try:
            task_id = str(uuid.uuid4())

            # Create task record
            task_record = {
                "task_id": task_id,
                "task_data": task_data,
                "target_agent": target_agent,
                "priority": priority.value,
                "created_at": datetime.now().isoformat(),
                "status": "queued"
            }

            # Add to task queue
            self.task_queue.append(task_record)

            # Process task immediately if high priority
            if priority in [AgentPriority.CRITICAL, AgentPriority.HIGH]:
                result = await self._process_task(task_record)
                return result
            else:
                # Return task ID for async processing
                return {
                    "task_id": task_id,
                    "status": "queued",
                    "estimated_completion": "within_5_minutes"
                }

        except Exception as e:
            self.logger.error(f"Failed to execute task: {e}")
            raise

    async def _process_task(self, task_record: dict[str, Any]) -> dict[str, Any]:
        """Process a specific task"""
        try:
            task_id = task_record["task_id"]
            task_data = task_record["task_data"]
            target_agent = task_record["target_agent"]

            # Update task status
            task_record["status"] = "processing"
            self.active_tasks[task_id] = task_record

            # Select agent(s) for task
            if target_agent:
                selected_agents = [target_agent]
            else:
                selected_agents = await self._select_agents_for_task(task_data)

            # Execute task with selected agents
            results = []
            for agent_id in selected_agents:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    try:
                        result = await agent.execute_task(task_data)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Agent {agent_id} failed to execute task: {e}")
                        results.append({
                            "agent_id": agent_id,
                            "status": "error",
                            "error": str(e)
                        })
                else:
                    self.logger.warning(f"Agent {agent_id} not found")

            # Update task status
            task_record["status"] = "completed"
            task_record["results"] = results
            task_record["completed_at"] = datetime.now().isoformat()

            # Move to completed tasks
            del self.active_tasks[task_id]
            self.completed_tasks.append(task_record)

            # Learn from task execution
            await self._learn_from_task_execution(task_record)

            return {
                "task_id": task_id,
                "status": "completed",
                "results": results,
                "agents_used": selected_agents
            }

        except Exception as e:
            self.logger.error(f"Failed to process task: {e}")
            task_record["status"] = "failed"
            task_record["error"] = str(e)
            return {
                "task_id": task_record["task_id"],
                "status": "failed",
                "error": str(e)
            }

    async def _select_agents_for_task(self, task_data: dict[str, Any]) -> list[str]:
        """Select the most appropriate agents for a task"""
        task_type = task_data.get("type", "unknown")
        required_capabilities = task_data.get("required_capabilities", [])

        # Find agents with required capabilities
        suitable_agents = []
        for agent_id, metadata in self.agent_metadata.items():
            if metadata["status"] == "active":
                agent_capabilities = set(metadata["capabilities"])
                if not required_capabilities or agent_capabilities.intersection(set(required_capabilities)):
                    suitable_agents.append(agent_id)

        # Score agents based on suitability
        agent_scores = []
        for agent_id in suitable_agents:
            score = await self._calculate_agent_suitability(agent_id, task_data)
            agent_scores.append((agent_id, score))

        # Sort by score and return top agents
        agent_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top 3 agents or all if less than 3
        return [agent_id for agent_id, score in agent_scores[:3]]

    async def _calculate_agent_suitability(self, agent_id: str, task_data: dict[str, Any]) -> float:
        """Calculate how suitable an agent is for a specific task"""
        try:
            metadata = self.agent_metadata[agent_id]
            health = self.agent_health[agent_id]

            # Base score from capabilities match
            task_capabilities = set(task_data.get("required_capabilities", []))
            agent_capabilities = set(metadata["capabilities"])
            capability_score = len(task_capabilities.intersection(agent_capabilities)) / max(len(task_capabilities), 1)

            # Health score
            health_score = health["performance_score"]

            # Priority score
            priority_scores = {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4,
                "background": 0.2
            }
            priority_score = priority_scores.get(metadata["priority"], 0.5)

            # Calculate weighted score
            final_score = (capability_score * 0.5 + health_score * 0.3 + priority_score * 0.2)

            return final_score

        except Exception as e:
            self.logger.error(f"Failed to calculate agent suitability: {e}")
            return 0.0

    async def request_collaboration(self, source_agent_id: str, target_agent_id: str,
                                  collaboration_data: dict[str, Any]) -> dict[str, Any]:
        """Request collaboration between two agents"""
        try:
            if target_agent_id not in self.agents:
                raise ValueError(f"Target agent {target_agent_id} not found")

            # Create collaboration request
            collaboration_id = str(uuid.uuid4())
            collaboration_request = {
                "id": collaboration_id,
                "source_agent": source_agent_id,
                "target_agent": target_agent_id,
                "data": collaboration_data,
                "timestamp": datetime.now().isoformat(),
                "status": "requested"
            }

            # Send request to target agent
            target_agent = self.agents[target_agent_id]

            # Create task for collaboration
            collaboration_task = {
                "type": "collaboration",
                "collaboration_id": collaboration_id,
                "source_agent": source_agent_id,
                "data": collaboration_data
            }

            # Execute collaboration task
            result = await target_agent.execute_task(collaboration_task)

            # Update collaboration request
            collaboration_request["status"] = "completed"
            collaboration_request["result"] = result

            # Store collaboration data
            if "collaborations" not in self.system_knowledge:
                self.system_knowledge["collaborations"] = []
            self.system_knowledge["collaborations"].append(collaboration_request)

            return {
                "collaboration_id": collaboration_id,
                "status": "completed",
                "result": result
            }

        except Exception as e:
            self.logger.error(f"Collaboration request failed: {e}")
            raise

    async def broadcast_message(self, channel: str, message: dict[str, Any]):
        """Broadcast a message to all agents or specific channel"""
        try:
            # Add broadcast channel if it doesn't exist
            if channel not in self.broadcast_channels:
                self.broadcast_channels.add(channel)

            # Add timestamp and message ID
            broadcast_message = {
                "id": str(uuid.uuid4()),
                "channel": channel,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "broadcast_type": "system"
            }

            # Send to all agents
            for agent_id in self.agents:
                if agent_id in self.message_bus:
                    self.message_bus[agent_id].append(broadcast_message)

            # Store in system knowledge
            if "broadcasts" not in self.system_knowledge:
                self.system_knowledge["broadcasts"] = []
            self.system_knowledge["broadcasts"].append(broadcast_message)

            self.logger.info(f"Message broadcasted on channel: {channel}")

        except Exception as e:
            self.logger.error(f"Failed to broadcast message: {e}")

    async def get_agent_status(self, agent_id: str) -> dict[str, Any] | None:
        """Get status of a specific agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            base_status = agent.get_status_report()

            # Add orchestrator metadata
            orchestrator_status = {
                **base_status,
                "ecosystem_metadata": self.agent_metadata[agent_id],
                "health_status": self.agent_health[agent_id],
                "message_queue_length": len(self.message_bus.get(agent_id, [])),
                "collaboration_partners": list(self.collaboration_networks.get(agent_id, set()))
            }

            return orchestrator_status

        return None

    async def get_system_overview(self) -> dict[str, Any]:
        """Get comprehensive system overview"""
        try:
            # Calculate system metrics
            total_agents = len(self.agents)
            active_agents = len([a for a in self.agents.values() if a.status.value == "active"])
            total_tasks = len(self.completed_tasks) + len(self.active_tasks)

            # Calculate overall health score
            health_scores = [h["performance_score"] for h in self.agent_health.values()]
            overall_health = sum(health_scores) / len(health_scores) if health_scores else 0.0

            # Get recent activity
            recent_tasks = self.completed_tasks[-10:] if self.completed_tasks else []
            recent_decisions = self.decision_history[-10:] if self.decision_history else []

            return {
                "system_status": "operational",
                "total_agents": total_agents,
                "active_agents": active_agents,
                "total_tasks_processed": total_tasks,
                "overall_health_score": overall_health,
                "recent_activity": {
                    "tasks": recent_tasks,
                    "decisions": recent_decisions
                },
                "system_knowledge_size": len(self.system_knowledge),
                "collaboration_networks": len(self.collaboration_networks),
                "workflow_chains": len(self.workflow_chains),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get system overview: {e}")
            return {"error": str(e)}

    async def _analyze_agent_dependencies(self, agent_id: str):
        """Analyze dependencies for a newly registered agent"""
        try:
            agent = self.agents[agent_id]
            metadata = self.agent_metadata[agent_id]

            # Analyze capabilities to determine dependencies
            dependencies = set()

            # Example dependency logic (in production, use more sophisticated analysis)
            if "data_analysis" in metadata["capabilities"]:
                # Data analysis agents might depend on data collection agents
                for other_id, other_metadata in self.agent_metadata.items():
                    if other_id != agent_id and "data_collection" in other_metadata["capabilities"]:
                        dependencies.add(other_id)

            if "decision_making" in metadata["capabilities"]:
                # Decision-making agents might depend on monitoring agents
                for other_id, other_metadata in self.agent_metadata.items():
                    if other_id != agent_id and "monitoring" in other_metadata["capabilities"]:
                        dependencies.add(other_id)

            self.agent_dependencies[agent_id] = dependencies

        except Exception as e:
            self.logger.error(f"Failed to analyze agent dependencies: {e}")

    async def _update_collaboration_networks(self, agent_id: str):
        """Update collaboration networks for a newly registered agent"""
        try:
            # Initialize collaboration network for new agent
            self.collaboration_networks[agent_id] = set()

            # Find potential collaboration partners based on capabilities
            agent_metadata = self.agent_metadata[agent_id]
            agent_capabilities = set(agent_metadata["capabilities"])

            for other_id, other_metadata in self.agent_metadata.items():
                if other_id != agent_id:
                    other_capabilities = set(other_metadata["capabilities"])

                    # Check for complementary capabilities
                    if agent_capabilities.intersection(other_capabilities):
                        # Add to collaboration networks
                        self.collaboration_networks[agent_id].add(other_id)
                        if other_id in self.collaboration_networks:
                            self.collaboration_networks[other_id].add(agent_id)
                        else:
                            self.collaboration_networks[other_id] = {agent_id}

        except Exception as e:
            self.logger.error(f"Failed to update collaboration networks: {e}")

    async def _cleanup_agent_dependencies(self, agent_id: str):
        """Clean up dependencies when an agent is unregistered"""
        try:
            # Remove from all dependency lists
            for deps in self.agent_dependencies.values():
                deps.discard(agent_id)

            # Remove agent's own dependencies
            if agent_id in self.agent_dependencies:
                del self.agent_dependencies[agent_id]

        except Exception as e:
            self.logger.error(f"Failed to cleanup agent dependencies: {e}")

    async def _cleanup_collaboration_networks(self, agent_id: str):
        """Clean up collaboration networks when an agent is unregistered"""
        try:
            # Remove from all collaboration networks
            for network in self.collaboration_networks.values():
                network.discard(agent_id)

            # Remove agent's own network
            if agent_id in self.collaboration_networks:
                del self.collaboration_networks[agent_id]

        except Exception as e:
            self.logger.error(f"Failed to cleanup collaboration networks: {e}")

    async def _learn_from_task_execution(self, task_record: dict[str, Any]):
        """Learn from task execution to improve future performance"""
        try:
            learning_data = {
                "task_type": task_record["task_data"].get("type", "unknown"),
                "agents_used": task_record.get("results", []),
                "execution_time": task_record.get("completed_at", ""),
                "success": task_record["status"] == "completed",
                "timestamp": datetime.now().isoformat()
            }

            self.learning_data.append(learning_data)

            # Keep only recent learning data
            if len(self.learning_data) > 1000:
                self.learning_data = self.learning_data[-1000:]

        except Exception as e:
            self.logger.error(f"Failed to learn from task execution: {e}")

    async def _system_monitoring(self):
        """Monitor system health and performance"""
        while True:
            try:
                # Update agent health
                for agent_id, agent in self.agents.items():
                    try:
                        # Get agent status
                        status = agent.get_status_report()

                        # Update health metrics
                        self.agent_health[agent_id].update({
                            "status": status["status"],
                            "last_check": datetime.now().isoformat(),
                            "performance_score": status["metrics"]["success_rate"],
                            "error_count": status["metrics"]["tasks_failed"]
                        })

                    except Exception as e:
                        self.logger.error(f"Failed to update health for agent {agent_id}: {e}")
                        self.agent_health[agent_id]["status"] = "error"
                        self.agent_health[agent_id]["error_count"] += 1

                # Calculate overall system health
                health_scores = [h["performance_score"] for h in self.agent_health.values()]
                overall_health = sum(health_scores) / len(health_scores) if health_scores else 0.0

                self.system_health = {
                    "overall_score": overall_health,
                    "agent_count": len(self.agents),
                    "healthy_agents": len([h for h in self.agent_health.values() if h["status"] == "healthy"]),
                    "last_updated": datetime.now().isoformat()
                }

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(60)

    async def _task_processing(self):
        """Process queued tasks"""
        while True:
            try:
                # Process tasks in queue
                if self.task_queue:
                    # Sort by priority
                    priority_order = ["critical", "high", "medium", "low", "background"]
                    self.task_queue.sort(key=lambda x: priority_order.index(x["priority"]))

                    # Process next task
                    task_record = self.task_queue.pop(0)
                    await self._process_task(task_record)

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                self.logger.error(f"Task processing error: {e}")
                await asyncio.sleep(5)

    async def _learning_cycle(self):
        """Periodic learning and knowledge update cycle"""
        while True:
            try:
                # Analyze learning data
                if len(self.learning_data) > 10:
                    await self._analyze_learning_data()

                # Update system knowledge
                await self._update_system_knowledge()

                await asyncio.sleep(300)  # Learning cycle every 5 minutes

            except Exception as e:
                self.logger.error(f"Learning cycle error: {e}")
                await asyncio.sleep(600)

    async def _optimization_cycle(self):
        """Periodic system optimization cycle"""
        while True:
            try:
                # Analyze system performance
                await self._analyze_system_performance()

                # Optimize agent assignments
                await self._optimize_agent_assignments()

                await asyncio.sleep(600)  # Optimization cycle every 10 minutes

            except Exception as e:
                self.logger.error(f"Optimization cycle error: {e}")
                await asyncio.sleep(1200)

    async def _analyze_learning_data(self):
        """Analyze learning data to identify patterns"""
        try:
            # Simple pattern analysis (in production, use ML models)
            successful_tasks = [t for t in self.learning_data if t["success"]]
            failed_tasks = [t for t in self.learning_data if not t["success"]]

            if successful_tasks:
                self.logger.info(f"Learning: {len(successful_tasks)} successful tasks, {len(failed_tasks)} failed tasks")

        except Exception as e:
            self.logger.error(f"Failed to analyze learning data: {e}")

    async def _update_system_knowledge(self):
        """Update system knowledge based on recent activities"""
        try:
            # Update knowledge based on completed tasks
            recent_tasks = self.completed_tasks[-100:] if self.completed_tasks else []

            # Extract insights from tasks
            task_insights = {
                "total_tasks": len(recent_tasks),
                "successful_tasks": len([t for t in recent_tasks if t["status"] == "completed"]),
                "common_task_types": {},
                "agent_performance": {}
            }

            # Analyze task types
            for task in recent_tasks:
                task_type = task["task_data"].get("type", "unknown")
                task_insights["common_task_types"][task_type] = task_insights["common_task_types"].get(task_type, 0) + 1

            # Update system knowledge
            self.system_knowledge["task_insights"] = task_insights

        except Exception as e:
            self.logger.error(f"Failed to update system knowledge: {e}")

    async def _analyze_system_performance(self):
        """Analyze overall system performance"""
        try:
            # Calculate performance metrics
            total_tasks = len(self.completed_tasks)
            successful_tasks = len([t for t in self.completed_tasks if t["status"] == "completed"])

            if total_tasks > 0:
                success_rate = successful_tasks / total_tasks

                self.performance_metrics = {
                    "total_tasks": total_tasks,
                    "successful_tasks": successful_tasks,
                    "success_rate": success_rate,
                    "average_tasks_per_minute": total_tasks / max(1, (datetime.now() - datetime.fromisoformat(self.completed_tasks[0]["created_at"])).total_seconds() / 60),
                    "last_updated": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Failed to analyze system performance: {e}")

    async def _optimize_agent_assignments(self):
        """Optimize agent assignments based on performance"""
        try:
            # Analyze agent performance
            agent_performance = {}
            for agent_id, health in self.agent_health.items():
                agent_performance[agent_id] = {
                    "performance_score": health["performance_score"],
                    "error_count": health["error_count"],
                    "status": health["status"]
                }

            # Identify underperforming agents
            underperforming = [aid for aid, perf in agent_performance.items()
                             if perf["performance_score"] < 0.7 or perf["error_count"] > 5]

            if underperforming:
                self.logger.warning(f"Underperforming agents identified: {underperforming}")

                # Could implement agent replacement or retraining logic here

        except Exception as e:
            self.logger.error(f"Failed to optimize agent assignments: {e}")

    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        self.logger.info("Shutting down Master Agent Ecosystem Orchestrator...")

        # Shutdown all agents
        for agent in self.agents.values():
            try:
                await agent.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down agent: {e}")

        self.logger.info("Master Agent Ecosystem Orchestrator shutdown complete")

# Global orchestrator instance
_master_orchestrator: MasterOrchestrator | None = None

def get_master_orchestrator() -> MasterOrchestrator:
    """Get the global master orchestrator instance"""
    global _master_orchestrator
    if _master_orchestrator is None:
        _master_orchestrator = MasterOrchestrator()
    return _master_orchestrator

def set_master_orchestrator(orchestrator: MasterOrchestrator):
    """Set the global master orchestrator instance"""
    global _master_orchestrator
    _master_orchestrator = orchestrator
