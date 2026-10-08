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
class DependencyEdge:
    """Represents a dependency connection from source file to target module."""

    source: str
    target: str
    is_internal: bool
    line_number: int = 1
    imported_symbols: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleNode:
    """A node in the internal dependency graph."""

    rel_path: str
    language: str
    dependencies: list[str] = field(default_factory=list)  # outgoing internal edges
    dependents: list[str] = field(default_factory=list)    # incoming internal edges
    external_dependencies: list[str] = field(default_factory=list)  # stdlib / 3rd-party
    symbol_count: int = 0

    @property
    def dependency_count(self) -> int:
        return len(self.dependencies)

    @property
    def dependent_count(self) -> int:
        return len(self.dependents)

    @property
    def connectivity(self) -> int:
        return self.dependency_count + self.dependent_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "rel_path": self.rel_path,
            "language": self.language,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "external_dependencies": self.external_dependencies,
            "dependency_count": self.dependency_count,
            "dependent_count": self.dependent_count,
            "connectivity": self.connectivity,
            "symbol_count": self.symbol_count,
        }


@dataclass
class EntryPointRecord:
    """Represents a detected application entry point with evidence."""

    rel_path: str
    reasons: list[str] = field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM
    category: str = "Application"  # CLI, Web Server, Script, Package Binary

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        return d


@dataclass
class HotspotRecord:
    """Represents an architecturally significant module based on connectivity and density."""

    rel_path: str
    dependent_count: int
    dependency_count: int
    symbol_count: int
    connectivity: int
    reasons: list[str] = field(default_factory=list)
    interpretation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArchitecturalLayer:
    """Represents an inferred architectural layer backed by repository evidence."""

    layer_name: str
    confidence: Confidence
    files: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        return d


@dataclass
class ReadingOrderItem:
    """A recommended step in the repository reading order."""

    order: int
    rel_path: str
    category: str
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingPhase:
    """A timed phase in the 30-minute contributor onboarding walkthrough."""

    time_window: str  # e.g., "0-3 min"
    focus: str        # e.g., "Project Vision & Scope"
    target_files: list[str]
    takeaway: str     # What you should understand after completing this step

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingPlan:
    """Complete 30-minute contributor onboarding blueprint."""

    project_name: str
    phases: list[OnboardingPhase] = field(default_factory=list)
    summary_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "phases": [p.to_dict() for p in self.phases],
            "summary_notes": self.summary_notes,
        }


@dataclass
class DependencyGraph:
    """Directed dependency graph across repository modules."""

    nodes: dict[str, ModuleNode] = field(default_factory=dict)
    edges: list[DependencyEdge] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "cycles": self.cycles,
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
