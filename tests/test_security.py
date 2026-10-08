"""Security tests ensuring RepoLens never executes repository code."""

from pathlib import Path
from repolens.engine import RepoLensEngine


def test_no_code_execution_security_guarantee(tmp_path: Path):
    """Verifies that malicious or arbitrary code in repository files is never executed."""
    canary_file = tmp_path / "canary_pwned.txt"

    # Malicious file attempting execution if imported or evaluated
    malicious_code = f"""
import os
from pathlib import Path

# If this file is imported or executed, it will create the canary file
Path(r"{canary_file}").write_text("VULNERABLE")

def normal_function():
    return 42
"""
    (tmp_path / "malicious.py").write_text(malicious_code, encoding="utf-8")
    (tmp_path / "setup.py").write_text("import sys; raise RuntimeError('setup.py executed!')", encoding="utf-8")

    engine = RepoLensEngine(tmp_path)
    result = engine.analyze()

    # The canary file must NOT exist!
    assert not canary_file.exists(), "CRITICAL SECURITY BREACH: Repository code was executed!"

    # Analysis succeeded statically
    assert result.scan.summary.total_files == 2
    analysis = result.analyses.get("malicious.py")
    assert analysis is not None
    assert any(s.name == "normal_function" for s in analysis.symbols)


def test_paths_with_spaces_and_special_chars(tmp_path: Path):
    """Verifies that paths with spaces work seamlessly on Windows and other OSes."""
    space_dir = tmp_path / "Folder With Spaces (and special chars)"
    space_dir.mkdir()

    (space_dir / "README.md").write_text("# Spaces\n", encoding="utf-8")
    (space_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")

    engine = RepoLensEngine(space_dir)
    result = engine.analyze()

    assert result.scan.summary.total_files == 2
    assert result.scan.summary.primary_language == "Python"


def test_empty_directory_handling(tmp_path: Path):
    """Verifies that an empty repository does not crash the analyzer."""
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()

    engine = RepoLensEngine(empty_dir)
    result = engine.analyze()

    assert result.scan.summary.total_files == 0
    assert result.scan.summary.total_lines == 0
    assert len(result.entry_points) == 0
    assert len(result.hotspots) == 0
