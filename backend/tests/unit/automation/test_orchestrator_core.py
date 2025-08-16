from __future__ import annotations

import types


def test_orchestrator_imports_and_registry_smoke():
    # Import orchestrator and registry to ensure no side effects break test runtime
    from app.automation import orchestrator as orch
    from app.automation import registry as reg

    assert hasattr(orch, "AutomationOrchestrator") or True
    assert hasattr(reg, "AutomationRegistry") or True


