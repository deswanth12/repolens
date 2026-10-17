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
    assert "repolens, version 0.1.2" in result.output


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


def test_cli_invalid_input_returns_nonzero():
    """Verifies that invalid or non-existent paths return appropriate non-zero exit codes."""
    runner = CliRunner()
    result = runner.invoke(main, ["non_existent_directory_12345"])
    assert result.exit_code != 0


def test_cli_unicode_and_spaces_json_output(tmp_path: Path):
    """Verifies that JSON output remains completely valid when paths contain spaces and Unicode characters."""
    special_dir = tmp_path / "Repo with spaces & 🚀 unicode"
    special_dir.mkdir()
    (special_dir / "módulo_principal.py").write_text("x = 'café'\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["report", str(special_dir), "--format", "json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert "summary" in data
    assert any("módulo_principal.py" in f["rel_path"] for f in data["files"])


def test_cli_python_m_execution():
    """Verifies that python -m repolens works seamlessly via __main__.py."""
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "-m", "repolens", "--version"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "repolens, version" in res.stdout


def test_cli_root_format_option(tmp_path: Path):
    """Verifies that the root CLI invocation accepts --format json directly."""
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "summary" in data
    assert "modules" in data
    assert "app.py" in data["modules"]


def test_cli_context_stdout(tmp_path: Path):
    """Verifies that repolens context outputs markdown to stdout."""
    (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["context", str(tmp_path)])
    assert result.exit_code == 0
    assert "# Codebase Intelligence:" in result.output
    assert "## 1. Project Profile & Scale" in result.output
    assert "## 2. Application Entry Points" in result.output
    assert "## 7. AI Agent Guardrails & Invariants" in result.output


def test_cli_context_output_file(tmp_path: Path):
    """Verifies that repolens context -o writes file to disk."""
    (tmp_path / "app.py").write_text("print('test')\n", encoding="utf-8")
    out_file = tmp_path / "AGENTS.md"

    runner = CliRunner()
    result = runner.invoke(main, ["context", str(tmp_path), "-o", str(out_file)])
    assert result.exit_code == 0
    assert "Wrote AI Context Pack" in result.output
    assert out_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "# Codebase Intelligence:" in content
    assert "## 1. Project Profile & Scale" in content


def test_cli_report_markdown(tmp_path: Path):
    """Verifies that repolens report --format markdown produces markdown output."""
    (tmp_path / "app.py").write_text("def fn(): pass\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["report", str(tmp_path), "--format", "markdown"])
    assert result.exit_code == 0
    assert "# Codebase Intelligence:" in result.output
    assert "## 1. Project Profile & Scale" in result.output


def test_cli_root_format_markdown(tmp_path: Path):
    """Verifies that the root CLI accepts --format markdown directly."""
    (tmp_path / "app.py").write_text("def fn(): pass\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--format", "markdown"])
    assert result.exit_code == 0
    assert "# Codebase Intelligence:" in result.output

