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


def test_extract_correlation_id_prefers_top_level():
    evt = {"correlation_id": "abc-123", "headers": {"correlation_id": "def"}}
    assert _mod().extract_correlation_id(evt) == "abc-123"


def test_extract_correlation_id_from_headers():
    evt = {"headers": {"correlation_id": "def"}}
    assert _mod().extract_correlation_id(evt) == "def"


def test_extract_correlation_id_from_meta():
    evt = {"meta": {"correlation_id": "ghi"}}
    assert _mod().extract_correlation_id(evt) == "ghi"


def test_extract_correlation_id_none():
    assert _mod().extract_correlation_id({}) is None

