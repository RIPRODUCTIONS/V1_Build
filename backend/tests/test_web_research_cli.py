import os

from tools.web_research.cli import main


def test_cli_disabled_exits_zero(capsys):
    os.environ.pop("RESEARCH_ENABLED", None)
    rc = main(["query here"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "disabled" in out.lower()


def test_cli_enabled_uses_fake_adapter(capsys):
    os.environ["RESEARCH_ENABLED"] = "1"
    rc = main(["fastapi"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Research results" in out
    assert "http" in out
