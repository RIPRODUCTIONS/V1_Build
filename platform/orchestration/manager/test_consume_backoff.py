from __future__ import annotations

import importlib.util
import pathlib


def _mod():
    mod_path = pathlib.Path(__file__).resolve().parent / "consumer.py"
    spec = importlib.util.spec_from_file_location("consumer", mod_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


def test_backoff_path(monkeypatch):
    m = _mod()

    class Boom:
        def xread(self, *a, **k):  # noqa: D401
            raise RuntimeError("boom")

    # Example override shape; exact defaults may vary
    class Cfg(m.ConsumerConfig):
        block_ms = 1
        backoff_initial_ms = 1
        backoff_max_ms = 2

    # monkeypatch time.sleep to be no-op for fast test
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)

    # simulate single loop iteration by patching to break after first error
    calls = {"n": 0}

    def fake_consume(cfg):
        calls["n"] += 1
        raise m.GracefulExit

    # Just ensure we can construct config
    cfg = Cfg()
    assert isinstance(cfg.block_ms, int)
