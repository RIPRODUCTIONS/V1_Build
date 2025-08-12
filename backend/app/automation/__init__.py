# Import all skills to ensure they get registered
# Import new Batch F modules
from app.automation import beat, learning, self_heal, tasks
from app.automation.orchestrator import run_dag

# Import core automation modules
from app.automation.registry import get_dag, get_skill, register_dag
from app.automation.router import router as automation_router
from app.automation.skills import ideation, research, research_validation

__all__ = [
    'get_dag',
    'get_skill',
    'register_dag',
    'run_dag',
    'automation_router',
    # Import modules for side effects (registration)
    'beat',
    'learning',
    'self_heal',
    'tasks',
    'ideation',
    'research',
    'research_validation',
]
