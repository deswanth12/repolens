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


class SymbolType(str, Enum):
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    CLASS = "class"
    METHOD = "method"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SymbolRecord:
    """Represents a defined symbol (function, class, method)."""

    name: str
    symbol_type: SymbolType
    line_number: int
    end_line_number: int
    parent_symbol: str | None = None
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    base_classes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["symbol_type"] = self.symbol_type.value
        return d


@dataclass
class ImportRecord:
    """Represents an imported module or symbol."""

    module: str
    imported_names: list[str] = field(default_factory=list)
    alias: str | None = None
    is_from: bool = False
    level: int = 0  # 0 for absolute, 1 for '.', 2 for '..', etc.
    line_number: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleAnalysis:
    """Analysis results for a single source file."""

    rel_path: str
    language: str
    symbols: list[SymbolRecord] = field(default_factory=list)
    imports: list[ImportRecord] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    has_main_block: bool = False
    parse_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rel_path": self.rel_path,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": [i.to_dict() for i in self.imports],
            "exports": self.exports,
            "has_main_block": self.has_main_block,
            "parse_error": self.parse_error,
        }


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
