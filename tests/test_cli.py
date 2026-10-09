"""Tests for the RepoLens CLI interface across all subcommands."""

import json
from pathlib import Path

from click.testing import CliRunner

from repolens import __version__
from repolens.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert f"repolens, version {__version__}" in result.output
    assert "repolens, version 0.1.1" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Understand how a codebase works" in result.output
    assert "scan" in result.output
    assert "onboard" in result.output
    assert "hotspots" in result.output
    assert "map" in result.output
    assert "explain" in result.output


def test_cli_full_report_terminal(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("def run():\n    pass\nif __name__ == '__main__':\n    run()\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "RepoLens" in result.output
    assert "RECOMMENDED READING ORDER" in result.output
    assert "APPLICATION ENTRY POINTS" in result.output


def test_cli_onboard_command(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('test')", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["onboard", str(tmp_path)])
    assert result.exit_code == 0
    assert "YOUR FIRST 30 MINUTES" in result.output
    assert "0-3 min" in result.output
    assert "README.md" in result.output


def test_cli_hotspots_command(tmp_path: Path):
    (tmp_path / "main.py").write_text("import utils\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text("def h(): pass\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["hotspots", str(tmp_path)])
    assert result.exit_code == 0
    assert "Structural Code Hotspots" in result.output


def test_cli_map_command(tmp_path: Path):
    (tmp_path / "main.py").write_text("from . import utils\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text("x = 1\n", encoding="utf-8")

    runner = CliRunner()
    res_mermaid = runner.invoke(main, ["map", str(tmp_path), "--format", "mermaid"])
    assert res_mermaid.exit_code == 0
    assert "graph TD" in res_mermaid.output

    res_dot = runner.invoke(main, ["map", str(tmp_path), "--format", "dot"])
    assert res_dot.exit_code == 0
    assert "digraph" in res_dot.output


def test_cli_explain_command(tmp_path: Path):
    (tmp_path / "service.py").write_text("class MyService:\n    def do_work(self): pass\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["explain", "service.py", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "RepoLens Explain: service.py" in result.output
    assert "MyService" in result.output


def test_cli_report_json(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("x = 10\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["report", str(tmp_path), "--format", "json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert "summary" in data
    assert "reading_order" in data
    assert "onboarding" in data
    assert "graph" in data


def test_cli_ignore_flag(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "secret.py").write_text("key = 'secret'\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "-i", "secret.py", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    scanned_files = [f["rel_path"] for f in data["files"]]
    assert "main.py" in scanned_files
    assert "secret.py" not in scanned_files
