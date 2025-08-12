from typing import Any

from app.automation.registry import skill
from app.prototype_builder.tasks import enqueue_build


@skill('prototype.enqueue_build')
async def prototype_enqueue(context: dict[str, Any]) -> dict[str, Any]:
    name = context.get('name') or 'Prototype'
    prompt = context.get('prompt') or 'Build something useful'
    run_id = await enqueue_build(name, prompt, repo_dir=context.get('repo_dir'))
    return {**context, 'prototype_run_id': run_id}
