"""Language detection and file category classification for RepoLens."""

from __future__ import annotations

import re
from pathlib import Path

from repolens.models import FileCategory

# Extension to language mapping
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyi": "Python",
    # JavaScript
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    # TypeScript
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".tsx": "TypeScript",
    # Other common programming languages
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    # Data & Configuration
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".xml": "XML",
    # Documentation
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".adoc": "AsciiDoc",
    ".txt": "Text",
}

BINARY_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".doc", ".docx",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo", ".pyd",
    ".jar", ".war", ".ear",
    ".db", ".sqlite", ".sqlite3",
}

# Config & Build file names
CONFIG_FILENAMES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "tsconfig.json",
    "jsconfig.json",
    "cargo.toml",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "makefile",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitignore",
    ".editorconfig",
    "tox.ini",
    ".flake8",
    "ruff.toml",
}

DOC_FILENAMES = {
    "readme",
    "contributing",
    "license",
    "changelog",
    "code_of_conduct",
    "security",
    "architecture",
}

TEST_DIR_PATTERNS = {"test", "tests", "spec", "specs", "__tests__"}


def detect_language(ext: str, filename: str) -> str:
    """Detects programming language from extension or special filename."""
    lower_name = filename.lower()
    if lower_name == "dockerfile" or lower_name.startswith("dockerfile."):
        return "Dockerfile"
    if lower_name == "makefile":
        return "Makefile"
    return EXTENSION_LANGUAGE_MAP.get(ext.lower(), "Unknown")


def classify_file(rel_path: str, ext: str, language: str) -> FileCategory:
    """Classifies a file into source, test, documentation, configuration, or other."""
    lower_path = rel_path.lower().replace("\\", "/")
    path_parts = lower_path.split("/")
    filename = path_parts[-1]
    name_stem = Path(filename).stem.lower()

    # 1. Binary files are always OTHER
    if ext.lower() in BINARY_EXTENSIONS:
        return FileCategory.OTHER

    # 2. Tests
    if any(part in TEST_DIR_PATTERNS for part in path_parts[:-1]):
        return FileCategory.TEST
    if filename.startswith("test_") or filename.endswith("_test.py"):
        return FileCategory.TEST
    if re.search(r"\.(test|spec)\.(js|ts|jsx|tsx)$", filename):
        return FileCategory.TEST

    # 3. Source code (check programming language source files)
    if language in {
        "Python",
        "JavaScript",
        "TypeScript",
        "Go",
        "Rust",
        "Java",
        "C",
        "C++",
        "C#",
        "Kotlin",
        "PHP",
        "Ruby",
        "Swift",
        "Scala",
        "Shell",
        "SQL",
    }:
        # Unless it's explicitly a config or build file like setup.py
        if filename.lower() in CONFIG_FILENAMES:
            return FileCategory.CONFIGURATION
        return FileCategory.SOURCE

    # 4. Documentation
    if ext.lower() in {".md", ".rst", ".adoc"}:
        return FileCategory.DOCUMENTATION
    if any(lower_path.startswith(d) for d in ("docs/", "doc/", "documentation/")):
        return FileCategory.DOCUMENTATION
    if ext.lower() in {".txt", ""} and (
        name_stem in DOC_FILENAMES
        or any(name_stem.startswith(f"{stem}_") or name_stem.startswith(f"{stem}-") for stem in DOC_FILENAMES)
    ):
        return FileCategory.DOCUMENTATION

    # 5. Configuration & Build
    if filename.lower() in CONFIG_FILENAMES:
        return FileCategory.CONFIGURATION
    if ext.lower() in {".toml", ".ini", ".cfg", ".yaml", ".yml", ".json"} and not any(
        lower_path.startswith(d) for d in ("src/", "lib/", "app/")
    ):
        return FileCategory.CONFIGURATION

    return FileCategory.OTHER


def is_binary_file(path: Path, ext: str) -> bool:
    """Checks if a file is binary using extension and byte inspection."""
    if ext.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
    except Exception:
        return False
    return False
