"""Fallback analyzer for unsupported programming languages.

Provides safe, honest structural information while explicitly noting that deep AST
analysis is limited for this language.
"""

from __future__ import annotations

import re
from pathlib import Path

from repolens.analyzers.base import BaseAnalyzer
from repolens.models import FileCategory, FileRecord, ImportRecord, ModuleAnalysis

SUPPORTED_LANGUAGES = {"Python", "JavaScript", "TypeScript"}

IMPORT_REGEXES = [
    # Go: import "fmt" or import ( "fmt" )
    re.compile(r"""import\s+(?:\(\s*([\s\S]*?)\s*\)|"([^"]+)")"""),
    # Rust: use std::collections::HashMap;
    re.compile(r"""use\s+([a-zA-Z0-9_:]+)"""),
    # Java / Kotlin: import java.util.List;
    re.compile(r"""import\s+(?:static\s+)?([a-zA-Z0-9_.*]+);?"""),
    # C / C++: #include <stdio.h> or #include "header.h"
    re.compile(r"""#include\s+[<"]([^>"]+)[>"]"""),
    # C#: using System;
    re.compile(r"""using\s+([a-zA-Z0-9_.]+);"""),
]


class FallbackAnalyzer(BaseAnalyzer):
    """Fallback analyzer providing limited structural info for unsupported languages."""

    @property
    def language_name(self) -> str:
        return "Unsupported Language Fallback"

    def can_analyze(self, file_record: FileRecord) -> bool:
        return (
            file_record.language not in SUPPORTED_LANGUAGES
            and file_record.category in {FileCategory.SOURCE, FileCategory.TEST}
            and not file_record.is_binary
        )

    def analyze(self, file_path: Path, rel_path: str) -> ModuleAnalysis:
        imports: list[ImportRecord] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for regex in IMPORT_REGEXES:
                for match in regex.finditer(content):
                    mod = match.group(1) or (match.group(2) if len(match.groups()) > 1 else None)
                    if mod:
                        # Clean multiple lines in Go block
                        for line in mod.splitlines():
                            clean = line.strip().strip('"')
                            if clean:
                                imports.append(ImportRecord(module=clean, line_number=1))
        except Exception:
            pass

        return ModuleAnalysis(
            rel_path=rel_path,
            language=file_path.suffix.lstrip(".") or "Unknown",
            symbols=[],
            imports=imports,
            exports=[],
            has_main_block=False,
            parse_error="Structural analysis is limited for this language.",
        )
