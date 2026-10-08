"""Tests for the RepoLens CLI interface."""

import json
from pathlib import Path
from click.testing import CliRunner

from repolens.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "repolens, version 0.1.0" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Understand how a codebase works" in result.output


def test_cli_scan_terminal_output(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "RepoLens" in result.output
    assert "Total Files:" in result.output
    assert "Python" in result.output


def test_cli_scan_json_output(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert "summary" in data
    assert "files" in data
    assert data["summary"]["total_files"] == 2
    assert data["summary"]["primary_language"] == "Python"
