"""Fallback analyzer for unsupported programming languages.

Provides safe, honest structural information while explicitly noting that deep AST
analysis is limited for this language.
"""

from __future__ import annotations

import re
from pathlib import Path

from repolens.analyzers.base import BaseAnalyzer
from repolens.discovery.language import detect_language
from repolens.models import FileCategory, FileRecord, ImportRecord, ModuleAnalysis

SUPPORTED_LANGUAGES = {"Python", "JavaScript", "TypeScript"}

LANGUAGE_IMPORT_REGEXES: dict[str, list[re.Pattern[str]]] = {
    "Go": [
        # import "fmt" or import ( "fmt" \n "os" )
        re.compile(r"""^[ \t]*import[ \t]+(?:\([ \t]*\n?([\s\S]*?)\n?[ \t]*\)|"([^"]+)")""", re.MULTILINE),
    ],
    "Rust": [
        # use std::collections::HashMap;
        re.compile(r"""^[ \t]*use[ \t]+([a-zA-Z0-9_:]+)""", re.MULTILINE),
    ],
    "Java": [
        re.compile(r"""^[ \t]*import[ \t]+(?:static[ \t]+)?([a-zA-Z0-9_.*]+);?""", re.MULTILINE),
    ],
    "Kotlin": [
        re.compile(r"""^[ \t]*import[ \t]+(?:static[ \t]+)?([a-zA-Z0-9_.*]+);?""", re.MULTILINE),
    ],
    "C": [
        re.compile(r"""^[ \t]*#include[ \t]+[<"]([^>"]+)[>"]""", re.MULTILINE),
    ],
    "C++": [
        re.compile(r"""^[ \t]*#include[ \t]+[<"]([^>"]+)[>"]""", re.MULTILINE),
    ],
    "C/C++ Header": [
        re.compile(r"""^[ \t]*#include[ \t]+[<"]([^>"]+)[>"]""", re.MULTILINE),
    ],
    "C++ Header": [
        re.compile(r"""^[ \t]*#include[ \t]+[<"]([^>"]+)[>"]""", re.MULTILINE),
    ],
    "C#": [
        re.compile(r"""^[ \t]*using[ \t]+([a-zA-Z0-9_.]+);""", re.MULTILINE),
    ],
    "Ruby": [
        re.compile(r"""^[ \t]*require(?:_relative)?[ \t]+['"]([^'"]+)['"]""", re.MULTILINE),
    ],
}


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
            and file_record.size_bytes <= 2 * 1024 * 1024
        )

    def analyze(self, file_path: Path, rel_path: str) -> ModuleAnalysis:
        lang = detect_language(file_path.suffix, file_path.name)
        if lang == "Unknown" and file_path.suffix:
            lang = file_path.suffix.lstrip(".")

        try:
            stat = file_path.stat()
            if stat.st_size > 2 * 1024 * 1024:
                return ModuleAnalysis(
                    rel_path=rel_path,
                    language=lang,
                    symbols=[],
                    imports=[],
                    exports=[],
                    has_main_block=False,
                    parse_error=f"File size ({stat.st_size} bytes) exceeds maximum parse limit (2097152 bytes).",
                )
        except OSError:
            pass

        imports: list[ImportRecord] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            regexes = LANGUAGE_IMPORT_REGEXES.get(lang, [])
            for regex in regexes:
                for match in regex.finditer(content):
                    mod = match.group(1) or (match.group(2) if len(match.groups()) > 1 else None)
                    if mod:
                        if lang == "Go":
                            # Clean multi-line Go block or single quoted import
                            for line in mod.splitlines():
                                quoted_match = re.search(r'"([^"]+)"', line)
                                if quoted_match:
                                    clean = quoted_match.group(1).strip()
                                    if clean:
                                        imports.append(ImportRecord(module=clean, line_number=1))
                                else:
                                    clean = line.strip().strip('"')
                                    if clean and not clean.startswith("//"):
                                        imports.append(ImportRecord(module=clean, line_number=1))
                        else:
                            clean = mod.strip().strip('"\'')
                            if clean:
                                imports.append(ImportRecord(module=clean, line_number=1))
        except Exception:
            pass

        return ModuleAnalysis(
            rel_path=rel_path,
            language=lang,
            symbols=[],
            imports=imports,
            exports=[],
            has_main_block=False,
            parse_error=None,
            analysis_mode="regex_fallback",
            warnings=["Structural analysis is limited for this language."],
        )
