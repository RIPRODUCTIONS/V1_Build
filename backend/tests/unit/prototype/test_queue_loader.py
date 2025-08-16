from __future__ import annotations

from app.prototype_builder.queue_loader import load_jobs


def test_queue_loader_returns_list():
    out = load_jobs()
    assert isinstance(out, list)

