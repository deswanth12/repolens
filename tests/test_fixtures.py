"""Integration tests running RepoLens against fixture repositories."""

from pathlib import Path

from repolens.engine import RepoLensEngine
from repolens.models import Confidence

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_fixture_python_cli():
    target = FIXTURES_DIR / "python_cli"
    engine = RepoLensEngine(target)
    result = engine.analyze()

    assert result.scan.summary.project_name == "python_cli"
    assert result.scan.summary.primary_language == "Python"
    assert len(result.entry_points) >= 1

    # Should detect mycli/main.py as entry point with HIGH confidence
    ep = next((e for e in result.entry_points if "main.py" in e.rel_path), None)
    assert ep is not None
    assert ep.confidence == Confidence.HIGH
    assert ep.category == "CLI" or "CLI" in ep.category

    # Reading order should place README first, then pyproject, then main.py
    assert result.reading_order[0].rel_path == "README.md"
    assert any("main.py" in item.rel_path for item in result.reading_order)


def test_fixture_python_layered():
    target = FIXTURES_DIR / "python_layered"
    engine = RepoLensEngine(target)
    result = engine.analyze()

    assert result.scan.summary.project_name == "python_layered"
    layer_names = {layer.layer_name for layer in result.layers}
    assert "API / Web Layer" in layer_names
    assert "Data Access / Storage" in layer_names
    assert "Tests" in layer_names

    # Hotspot detection should pick up models or auth service
    assert len(result.hotspots) >= 1


def test_fixture_javascript_app():
    target = FIXTURES_DIR / "javascript_app"
    engine = RepoLensEngine(target)
    result = engine.analyze()

    assert result.scan.summary.project_name == "javascript_app"
    assert result.scan.summary.primary_language == "JavaScript"
    assert len(result.entry_points) >= 1

    # Should detect bin/run.js from package.json or index.js
    assert any("run.js" in ep.rel_path or "index.js" in ep.rel_path for ep in result.entry_points)


def test_fixture_typescript_app():
    target = FIXTURES_DIR / "typescript_app"
    engine = RepoLensEngine(target)
    result = engine.analyze()

    assert result.scan.summary.project_name == "typescript_app"
    assert result.scan.summary.primary_language == "TypeScript"
    assert len(result.entry_points) >= 1
    assert any("index.ts" in ep.rel_path for ep in result.entry_points)


def test_fixture_malformed():
    target = FIXTURES_DIR / "malformed"
    engine = RepoLensEngine(target)
    # Scan and analysis should not raise exceptions or crash
    result = engine.analyze()

    assert result.scan.summary.project_name == "malformed"
    # Malformed python file should report parse_error
    broken_py = result.analyses.get("broken_syntax.py")
    assert broken_py is not None
    assert broken_py.parse_error is not None
    assert "Syntax error" in broken_py.parse_error


def test_fixture_unsupported():
    target = FIXTURES_DIR / "unsupported"
    engine = RepoLensEngine(target)
    result = engine.analyze()

    assert result.scan.summary.project_name == "unsupported"
    assert result.scan.summary.total_files == 2
    go_analysis = result.analyses.get("main.go")
    assert go_analysis is not None
    assert "Structural analysis is limited" in (go_analysis.parse_error or "")
