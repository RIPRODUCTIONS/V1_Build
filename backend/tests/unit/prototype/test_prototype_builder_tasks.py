from __future__ import annotations

def test_enqueue_build_returns_run_id(monkeypatch):
    from app.prototype_builder import tasks as t

    class _Celery:
        def send_task(self, *a, **k):  # noqa: ANN001
            return None

    monkeypatch.setattr(t, "celery_app", _Celery())
    rid = t.app_run(t.enqueue_build("demo", "prompt"))
    assert isinstance(rid, str) and len(rid) > 10


def test_build_task_inline_returns_true(monkeypatch):
    from app.prototype_builder.tasks import _build_task

    def _verify(obj):  # noqa: ANN001
        return {"ok": True, "id": obj.get("id")}

    monkeypatch.setattr("app.prototype_builder.verification_engine.verify", _verify)
    assert _build_task("r1", "demo", "p", None) is True


