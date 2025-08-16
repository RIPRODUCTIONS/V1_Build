from __future__ import annotations

from app.tasks.investigation_tasks import run_sca_scan, run_apt_attribution


def test_sca_scan_apply_path_success():
    res = run_sca_scan.apply(args=[{"project": "backend/", "task_id": None}]).result
    assert res["success"] is True
    assert isinstance(res.get("findings"), list)


def test_apt_attribution_apply_path_success():
    res = run_apt_attribution.apply(args=[{"candidate_groups": ["APT28", "APT1"], "evidence": {"infrastructure": True}, "task_id": None}]).result
    assert res["success"] is True
    assert isinstance(res.get("results"), list) and res["results"]


