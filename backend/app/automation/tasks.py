from __future__ import annotations

import time
from typing import Any

from app.automation.celery_app import celery
from app.automation.orchestrator import run_dag
from app.automation.state import set_status
from app.obs.metrics import AUTONOMOUS_LAST_RUN_TIMESTAMP, AUTONOMOUS_RUNS_TOTAL
from app.services.queue.redis_bus import get_bus


@celery.task(name='automation.run_full_pipeline_autonomous')
def run_full_pipeline_autonomous(topic: str) -> dict[str, Any]:
    """Autonomous task that runs the full idea → research pipeline."""

    try:
        # Increment autonomous run counter
        AUTONOMOUS_RUNS_TOTAL.labels(status='started').inc()

        # Create correlation ID for this autonomous run
        correlation_id = f'autonomous_{int(time.time())}'

        # Step 1: Generate ideas
        idea_run_id = str(time.time())
        set_status(
            idea_run_id,
            'started',
            {'intent': 'ideation.generate', 'correlation_id': correlation_id, 'autonomous': True},
        )

        # Run idea generation
        idea_context = {
            'topic': topic,
            'count': 5,
            'correlation_id': correlation_id,
            'autonomous': True,
        }

        idea_result = run_dag(idea_run_id, ['ideation.generate'], idea_context)

        # Step 2: Validate the best idea
        if idea_result and idea_result.get('ideas'):
            # Take the first idea for validation
            best_idea = idea_result['ideas'][0]

            validate_run_id = str(time.time())
            set_status(
                validate_run_id,
                'started',
                {
                    'intent': 'research.validate_idea',
                    'correlation_id': correlation_id,
                    'autonomous': True,
                },
            )

            # Run research validation
            validate_context = {
                'idea': best_idea,
                'correlation_id': correlation_id,
                'run_id': idea_run_id,
                'autonomous': True,
            }

            run_dag(validate_run_id, ['research.validate_idea'], validate_context)

            # Emit completion event
            bus = get_bus()
            if bus:
                bus.emit(
                    'automation.autonomous_completed',
                    {
                        'correlation_id': correlation_id,
                        'idea_run_id': idea_run_id,
                        'validate_run_id': validate_run_id,
                        'topic': topic,
                        'timestamp': time.time(),
                    },
                )

            # Update metrics
            AUTONOMOUS_RUNS_TOTAL.labels(status='completed').inc()
            AUTONOMOUS_LAST_RUN_TIMESTAMP.labels(department='ideation').set(time.time())

            return {
                'status': 'completed',
                'correlation_id': correlation_id,
                'idea_run_id': idea_run_id,
                'validate_run_id': validate_run_id,
                'topic': topic,
            }
        else:
            # No ideas generated
            AUTONOMOUS_RUNS_TOTAL.labels(status='failed').inc()
            return {
                'status': 'failed',
                'correlation_id': correlation_id,
                'error': 'No ideas generated',
            }

    except Exception as e:
        AUTONOMOUS_RUNS_TOTAL.labels(status='failed').inc()
        raise e


def trigger_idea_engine(topic: str, count: int = 5) -> str:
    """Helper to trigger idea engine and return run ID."""
    # This would integrate with your existing automation router
    # For now, return a placeholder
    return f'idea_run_{int(time.time())}'


def wait_and_get_first_idea(run_id: str) -> dict[str, Any]:
    """Helper to wait for idea generation and get first result."""
    # This would poll the run status and extract artifacts
    # For now, return a placeholder
    return {
        'title': 'AI-driven personal finance automation',
        'description': 'Automated financial planning and investment management',
        'market_size': 'large',
        'complexity': 'medium',
    }


def trigger_research_validate(idea: dict[str, Any]) -> str:
    """Helper to trigger research validation and return run ID."""
    # This would integrate with your existing research router
    # For now, return a placeholder
    return f'validate_run_{int(time.time())}'
