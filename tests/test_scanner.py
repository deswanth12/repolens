"""Tests for repository discovery, ignore filters, and language detection."""

from pathlib import Path
import pytest

from repolens.discovery.ignore import IgnoreFilter
from repolens.discovery.language import (
    classify_file,
    detect_language,
    is_binary_file,
)
from repolens.discovery.scanner import RepositoryScanner
from repolens.models import FileCategory


def test_language_detection():
    assert detect_language(".py", "main.py") == "Python"
    assert detect_language(".ts", "app.ts") == "TypeScript"
    assert detect_language(".js", "index.js") == "JavaScript"
    assert detect_language(".go", "server.go") == "Go"
    assert detect_language(".rs", "lib.rs") == "Rust"
    assert detect_language("", "Dockerfile") == "Dockerfile"
    assert detect_language("", "Makefile") == "Makefile"
    assert detect_language(".xyz123", "weird.xyz123") == "Unknown"


def test_file_classification():
    assert classify_file("src/main.py", ".py", "Python") == FileCategory.SOURCE
    assert classify_file("tests/test_main.py", ".py", "Python") == FileCategory.TEST
    assert classify_file("src/app.test.ts", ".ts", "TypeScript") == FileCategory.TEST
    assert classify_file("README.md", ".md", "Markdown") == FileCategory.DOCUMENTATION
    assert classify_file("docs/guide.md", ".md", "Markdown") == FileCategory.DOCUMENTATION
    assert classify_file("pyproject.toml", ".toml", "TOML") == FileCategory.CONFIGURATION
    assert classify_file("package.json", ".json", "JSON") == FileCategory.CONFIGURATION


def test_ignore_filter_default_dirs(tmp_path: Path):
    filter_ = IgnoreFilter(tmp_path)
    assert filter_.is_dir_ignored(".git", ".git") is True
    assert filter_.is_dir_ignored("node_modules", "node_modules") is True
    assert filter_.is_dir_ignored(".venv", ".venv") is True
    assert filter_.is_dir_ignored("__pycache__", "src/__pycache__") is True
    assert filter_.is_dir_ignored("src", "src") is False


def test_ignore_filter_custom_and_gitignore(tmp_path: Path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\nsecret_dir/\n", encoding="utf-8")

    filter_ = IgnoreFilter(tmp_path, respect_gitignore=True)
    assert filter_.is_file_ignored("app.log", "logs/app.log") is True
    assert filter_.is_dir_ignored("secret_dir", "secret_dir") is True
    assert filter_.is_file_ignored("app.py", "app.py") is False


def test_scanner_end_to_end(tmp_path: Path):
    # Setup mock repo structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "node_modules").mkdir()

    (tmp_path / "README.md").write_text("# Mock Project\nWelcome!\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'mock'\n", encoding="utf-8")
    (tmp_path / "src" / "main.py").write_text("def run():\n    print('hi')\n", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def helper():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests" / "test_main.py").write_text("def test_run():\n    assert True\n", encoding="utf-8")
    (tmp_path / "node_modules" / "leak.js").write_text("console.log('ignored');", encoding="utf-8")

    scanner = RepositoryScanner(tmp_path)
    result = scanner.scan()

    assert result.summary.project_name == tmp_path.name
    assert result.summary.total_files == 5  # README, pyproject, main, utils, test_main
    assert result.summary.source_files == 2  # main, utils
    assert result.summary.test_files == 1   # test_main
    assert result.summary.doc_files == 1    # README
    assert result.summary.config_files == 1 # pyproject.toml
    assert result.summary.primary_language == "Python"
    assert result.summary.ignored_count >= 1  # node_modules was ignored


def test_scanner_nonexistent_path(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist"
    scanner = RepositoryScanner(non_existent)
    with pytest.raises(FileNotFoundError):
        scanner.scan()
