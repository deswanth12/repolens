"""Core data models for RepoLens.

Uses Python dataclasses for lightweight, clean, dependency-free models
with built-in serialization helpers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class FileCategory(str, Enum):
    SOURCE = "source"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    BUILD = "build"
    OTHER = "other"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FileRecord:
    """Represents a discovered file in the repository."""

    rel_path: str  # POSIX-style relative path from repo root
    extension: str
    language: str
    category: FileCategory
    size_bytes: int
    line_count: int = 0
    is_binary: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d


@dataclass
class LanguageStats:
    """Summary statistics for a programming language detected in the repo."""

    language: str
    file_count: int
    line_count: int
    percentage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanSummary:
    """High-level summary of the repository scan."""

    root_path: str
    project_name: str
    is_git: bool
    total_files: int
    source_files: int
    test_files: int
    doc_files: int
    config_files: int
    total_lines: int
    primary_language: str
    languages: list[LanguageStats] = field(default_factory=list)
    ignored_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["languages"] = [lang.to_dict() for lang in self.languages]
        return d


@dataclass
class RepositoryScanResult:
    """Complete scan result containing file records and summary."""

    summary: ScanSummary
    files: list[FileRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "files": [f.to_dict() for f in self.files],
        }
