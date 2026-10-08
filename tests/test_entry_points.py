"""Tests for the Entry Point Detection engine."""

from pathlib import Path
from repolens.intelligence.entry_points import EntryPointDetector
from repolens.models import Confidence, ModuleAnalysis, SymbolRecord, SymbolType


def test_entry_point_main_block(tmp_path: Path):
    analyses = {
        "app/server.py": ModuleAnalysis(
            rel_path="app/server.py",
            language="Python",
            has_main_block=True,
            symbols=[
                SymbolRecord(
                    name="main",
                    symbol_type=SymbolType.FUNCTION,
                    line_number=10,
                    end_line_number=20,
                )
            ],
        ),
        "app/utils.py": ModuleAnalysis(
            rel_path="app/utils.py",
            language="Python",
            has_main_block=False,
            symbols=[
                SymbolRecord(
                    name="helper",
                    symbol_type=SymbolType.FUNCTION,
                    line_number=1,
                    end_line_number=5,
                )
            ],
        ),
    }

    detector = EntryPointDetector(tmp_path, analyses)
    results = detector.detect()

    assert len(results) == 1
    ep = results[0]
    assert ep.rel_path == "app/server.py"
    assert ep.confidence == Confidence.HIGH
    assert any("__main__" in r for r in ep.reasons)


def test_entry_point_pyproject_scripts(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "mytool"
version = "0.1.0"

[project.scripts]
mytool = "mytool.cli:main"
""",
        encoding="utf-8",
    )

    analyses = {
        "mytool/cli.py": ModuleAnalysis(
            rel_path="mytool/cli.py",
            language="Python",
            symbols=[
                SymbolRecord(
                    name="main",
                    symbol_type=SymbolType.FUNCTION,
                    line_number=5,
                    end_line_number=15,
                    decorators=["click.command"],
                )
            ],
        ),
    }

    detector = EntryPointDetector(tmp_path, analyses)
    results = detector.detect()

    assert len(results) == 1
    ep = results[0]
    assert ep.rel_path == "mytool/cli.py"
    assert ep.confidence == Confidence.HIGH
    assert any("pyproject.toml" in r for r in ep.reasons)
    assert any("click" in r.lower() for r in ep.reasons)


def test_entry_point_filename_convention(tmp_path: Path):
    analyses = {
        "main.py": ModuleAnalysis(
            rel_path="main.py",
            language="Python",
            has_main_block=False,
            symbols=[],
        ),
    }

    detector = EntryPointDetector(tmp_path, analyses)
    results = detector.detect()

    assert len(results) == 1
    assert results[0].rel_path == "main.py"
    assert results[0].confidence == Confidence.MEDIUM
