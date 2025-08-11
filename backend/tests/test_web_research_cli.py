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


def test_cli_offline_and_stats(capsys, tmp_path):
    os.environ["RESEARCH_ENABLED"] = "1"
    os.environ["RESEARCH_STATS"] = "1"
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    # minimal index and one page
    (fixtures / "search_index.json").write_text(
        '{"hello world": ["https://example.com/x.html"]}', encoding="utf-8"
    )
    (fixtures / "example_com_x_html.html").write_text(
        "<html><head><title>X</title></head><body><p>Hi</p></body></html>", encoding="utf-8"
    )
    rc = main(["hello world", "--offline", "--fixtures-path", str(fixtures), "--stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "== research stats ==" in out
