"""Base analyzer interface for language parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from repolens.models import FileRecord, ModuleAnalysis


class BaseAnalyzer(ABC):
    """Abstract base class for language-specific AST analyzers."""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Name of the programming language handled by this analyzer."""
        pass

    @abstractmethod
    def can_analyze(self, file_record: FileRecord) -> bool:
        """Determines if this analyzer can process the given file."""
        pass

    @abstractmethod
    def analyze(self, file_path: Path, rel_path: str) -> ModuleAnalysis:
        """Parses the file and extracts symbols, imports, and module metadata."""
        pass
