"""Ignore engine for RepoLens.

Respects .gitignore rules and enforces sensible default exclusions for
virtual environments, package directories, caches, and build artifacts.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pathspec

DEFAULT_IGNORE_DIRS = {
    # Version control
    ".git",
    ".svn",
    ".hg",
    # Package dependencies
    "node_modules",
    "vendor",
    "bower_components",
    # Virtual environments
    ".venv",
    "venv",
    "env",
    "ENV",
    ".env",
    # Python caches & build artifacts
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    "eggs",
    ".eggs",
    # JavaScript / TypeScript build
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    # Java / Rust / Go / C# build
    "target",
    "bin",
    "obj",
    # Coverage & test output
    "coverage",
    ".nyc_output",
    "htmlcov",
    # IDE & system
    ".idea",
    ".vscode",
}

DEFAULT_IGNORE_FILES = {
    ".DS_Store",
    "Thumbs.db",
    ".env",
    ".env.local",
    ".env.development",
    ".env.test",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
    "credentials.json",
    "service-account.json",
    "client_secret.json",
}


class IgnoreFilter:
    """Evaluates whether a relative file or directory path should be ignored."""

    def __init__(
        self,
        root_path: Path,
        custom_patterns: Iterable[str] | None = None,
        respect_gitignore: bool = True,
    ) -> None:
        self.root_path = root_path
        self.custom_patterns = list(custom_patterns or [])
        self.spec: pathspec.PathSpec | None = None

        if respect_gitignore:
            self._load_gitignore()

    def _load_gitignore(self) -> None:
        gitignore_path = self.root_path / ".gitignore"
        lines: list[str] = []
        if gitignore_path.is_file():
            try:
                content = gitignore_path.read_text(encoding="utf-8", errors="replace")
                lines.extend(content.splitlines())
            except Exception:
                pass
        if self.custom_patterns:
            lines.extend(self.custom_patterns)

        if lines:
            self.spec = pathspec.PathSpec.from_lines("gitignore", lines)

    def is_dir_ignored(self, dir_name: str, rel_path: str) -> bool:
        """Fast check for directories during os.walk."""
        if dir_name in DEFAULT_IGNORE_DIRS:
            return True
        if dir_name.endswith(".egg-info"):
            return True
        if self.spec:
            # pathspec expects trailing slash for directories to match directory rules
            norm_path = rel_path.replace("\\", "/").strip("/") + "/"
            if self.spec.match_file(norm_path):
                return True
        return False

    def is_file_ignored(self, file_name: str, rel_path: str) -> bool:
        """Check for files during walk."""
        if file_name in DEFAULT_IGNORE_FILES:
            return True
        if file_name.startswith(".env.") or file_name.endswith(".env"):
            return True
        if file_name.endswith((".pyc", ".pyo", ".pyd")):
            return True
        if self.spec:
            norm_path = rel_path.replace("\\", "/").strip("/")
            if self.spec.match_file(norm_path):
                return True
        return False
