"""Tests for the RepoLens CLI interface across all subcommands."""

import json
from pathlib import Path

from click.testing import CliRunner

from repolens import __version__
from repolens.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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


def test_cli_schema_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--schema"])
    assert result.exit_code == 0

    schema = json.loads(result.output)
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["type"] == "object"
    for prop in ("summary", "entry_points", "reading_order", "hotspots", "architecture", "onboarding", "graph", "files", "modules"):
        assert prop in schema["properties"]
        assert prop in schema["required"]


_JSON_TYPES = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}


def _schema_violations(schema: dict, value, path: str = "$") -> list[str]:
    """Check `value` against the subset of JSON Schema REPORT_JSON_SCHEMA uses.

    Beyond plain validation, an object key the schema does not declare is also
    reported, so a field added to a `to_dict()` without a schema update fails.
    """
    errors = []
    types = schema.get("type")
    if types is not None:
        types = types if isinstance(types, list) else [types]
        if not any(_JSON_TYPES[t](value) for t in types):
            return [f"{path}: expected {types}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, dict):
        props = schema.get("properties")
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required '{key}'")
        if props is not None:
            for key, sub in value.items():
                if key not in props:
                    errors.append(f"{path}: undeclared field '{key}'")
                else:
                    errors += _schema_violations(props[key], sub, f"{path}.{key}")
        elif isinstance(schema.get("additionalProperties"), dict):
            for key, sub in value.items():
                errors += _schema_violations(schema["additionalProperties"], sub, f"{path}[{key!r}]")
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(value):
            errors += _schema_violations(schema["items"], item, f"{path}[{i}]")
    return errors


def _schema_and_layered_report():
    runner = CliRunner()
    schema_result = runner.invoke(main, ["--schema"])
    report_result = runner.invoke(main, ["--format", "json", str(FIXTURES_DIR / "python_layered")])
    assert schema_result.exit_code == 0
    assert report_result.exit_code == 0
    return json.loads(schema_result.output), json.loads(report_result.output)


def test_cli_schema_matches_full_report_structure():
    schema, report = _schema_and_layered_report()

    # The fixture must exercise the nested schemas, not just empty lists.
    assert report["files"] and report["modules"] and report["graph"]["nodes"]
    assert report["architecture"] and report["hotspots"]

    assert _schema_violations(schema, report) == []


def test_cli_schema_rejects_incomplete_nested_object():
    schema, report = _schema_and_layered_report()
    module = next(iter(report["modules"]))
    del report["summary"]["total_files"]
    del report["modules"][module]["imports"]

    assert _schema_violations(schema, report) == [
        "$.summary: missing required 'total_files'",
        f"$.modules[{module!r}]: missing required 'imports'",
    ]


def test_cli_schema_rejects_undeclared_nested_field():
    schema, report = _schema_and_layered_report()
    report["hotspots"][0]["new_metric"] = 1

    assert _schema_violations(schema, report) == ["$.hotspots[0]: undeclared field 'new_metric'"]


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

