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


def test_file_symlinks_pointing_outside_root_are_never_read(tmp_path: Path):
    """Verifies that symlinks targeting files outside the repository root are strictly blocked and excluded."""
    external_dir = tmp_path / "external_private_secrets"
    external_dir.mkdir()
    secret_file = external_dir / "secret_outside.py"
    secret_file.write_text("SUPER_SECRET_EXTERNAL_CREDENTIAL = 'dont_read_me'\n", encoding="utf-8")

    repo_dir = tmp_path / "repo_root"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("print('inside repo')\n", encoding="utf-8")

    escape_link = repo_dir / "symlink_escape.py"
    dir_escape_link = repo_dir / "ext_dir_link"
    try:
        escape_link.symlink_to(secret_file)
        dir_escape_link.symlink_to(external_dir)
    except OSError:
        import pytest

        pytest.skip("Symlink creation not supported on this platform")

    engine = RepoLensEngine(repo_dir)
    result = engine.analyze()

    # The external symlink must NOT be cataloged as a source file
    scanned_paths = [f.rel_path for f in result.scan.files]
    assert "symlink_escape.py" not in scanned_paths
    assert "secret_outside.py" not in scanned_paths
    assert "ext_dir_link" not in scanned_paths

    # Its contents must NEVER enter analyses or report
    assert "symlink_escape.py" not in result.analyses
    for analysis in result.analyses.values():
        for s in analysis.symbols:
            assert s.name != "SUPER_SECRET_EXTERNAL_CREDENTIAL"

    # A warning must be recorded noting the boundary escape
    escape_warnings = [w for w in result.scan.summary.warnings if "escaping repository root" in w]
    assert len(escape_warnings) >= 1


def test_broken_symlinks_and_unreadable_files_produce_warnings(tmp_path: Path):
    """Verifies that broken symlinks and unreadable targets produce warnings without crashing."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "app.py").write_text("x = 1\n", encoding="utf-8")

    broken_link = repo_dir / "broken.py"
    try:
        broken_link.symlink_to(repo_dir / "nonexistent_target.py")
    except OSError:
        import pytest

        pytest.skip("Symlink creation not supported on this platform")

    engine = RepoLensEngine(repo_dir)
    result = engine.analyze()

    assert result.scan.summary.total_files == 1
    assert any("broken.py" in w or "escaping" in w or "symlink" in w for w in result.scan.summary.warnings)


def test_oversized_files_skipped_for_ast_parsing(tmp_path: Path):
    """Verifies that files exceeding 2 MiB are skipped for AST parsing and receive clean parse_error notes."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # 1. Normal file
    (repo_dir / "normal.py").write_text("def hello(): return 1\n", encoding="utf-8")

    # 2. Oversized Python file (> 2 MiB)
    oversized_py = repo_dir / "huge.py"
    chunk = "# comment\n" * 1024  # ~10 KB
    with open(oversized_py, "w", encoding="utf-8") as f:
        # Write ~2.1 MB
        for _ in range(215):
            f.write(chunk)
        f.write("def should_not_be_parsed(): pass\n")

    # 3. Oversized TypeScript file (> 2 MiB)
    oversized_ts = repo_dir / "huge.ts"
    with open(oversized_ts, "w", encoding="utf-8") as f:
        for _ in range(215):
            f.write(chunk)
        f.write("export function hugeTs() { return true; }\n")

    engine = RepoLensEngine(repo_dir)
    result = engine.analyze()

    # normal.py was parsed
    assert "normal.py" in result.analyses
    assert result.analyses["normal.py"].parse_error is None
    assert any(s.name == "hello" for s in result.analyses["normal.py"].symbols)

    # huge.py was skipped for AST parsing
    assert "huge.py" in result.analyses
    huge_py_analysis = result.analyses["huge.py"]
    assert huge_py_analysis.parse_error is not None
    assert "exceeds maximum AST parse limit" in huge_py_analysis.parse_error
    assert len(huge_py_analysis.symbols) == 0

    # huge.ts was skipped for AST parsing
    assert "huge.ts" in result.analyses
    huge_ts_analysis = result.analyses["huge.ts"]
    assert huge_ts_analysis.parse_error is not None
    assert "exceeds maximum AST parse limit" in huge_ts_analysis.parse_error
    assert len(huge_ts_analysis.symbols) == 0

    # Warnings recorded in summary
    assert any("huge.py" in w and "exceeds limit" in w for w in result.scan.summary.warnings)
    assert any("huge.ts" in w and "exceeds limit" in w for w in result.scan.summary.warnings)

