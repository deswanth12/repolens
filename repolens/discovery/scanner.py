"""Repository scanner for RepoLens.

Traverses the repository filesystem, applies ignore rules, classifies files,
computes language statistics, and produces a structured scan result.
"""

from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from repolens.discovery.ignore import IgnoreFilter
from repolens.discovery.language import (
    classify_file,
    detect_language,
    is_binary_file,
)
from repolens.models import (
    FileCategory,
    FileRecord,
    LanguageStats,
    RepositoryScanResult,
    ScanSummary,
)

# Maximum file size to attempt counting lines (2 MB)
MAX_LINE_COUNT_SIZE = 2 * 1024 * 1024


class RepositoryScanner:
    """Discovers and catalogs repository structure and files."""

    def __init__(
        self,
        root_path: str | Path,
        custom_ignores: Iterable[str] | None = None,
        respect_gitignore: bool = True,
    ) -> None:
        self.root_path = Path(root_path).resolve()
        self.custom_ignores = list(custom_ignores or [])
        self.respect_gitignore = respect_gitignore
        self.ignore_filter = IgnoreFilter(
            self.root_path,
            custom_patterns=self.custom_ignores,
            respect_gitignore=self.respect_gitignore,
        )

    def scan(self) -> RepositoryScanResult:
        """Executes repository scan."""
        if not self.root_path.exists() or not self.root_path.is_dir():
            raise FileNotFoundError(f"Path does not exist or is not a directory: {self.root_path}")

        project_name = self.root_path.name
        is_git = (self.root_path / ".git").exists()

        file_records: list[FileRecord] = []
        ignored_count = 0
        warnings: list[str] = []

        lang_file_counts: dict[str, int] = defaultdict(int)
        lang_line_counts: dict[str, int] = defaultdict(int)

        category_counts: dict[FileCategory, int] = defaultdict(int)
        total_lines = 0

        for root, dirs, files in os.walk(self.root_path, topdown=True):
            current_dir = Path(root)
            try:
                rel_dir = current_dir.relative_to(self.root_path).as_posix()
            except ValueError:
                continue

            # Prune ignored directories in-place
            dirs_to_remove = []
            for d in dirs:
                sub_rel = f"{rel_dir}/{d}" if rel_dir != "." else d
                if self.ignore_filter.is_dir_ignored(d, sub_rel):
                    dirs_to_remove.append(d)
                    ignored_count += 1

            for d in dirs_to_remove:
                dirs.remove(d)

            # Process files in current directory
            for f in files:
                file_path = current_dir / f
                rel_file = f"{rel_dir}/{f}" if rel_dir != "." else f

                if self.ignore_filter.is_file_ignored(f, rel_file):
                    ignored_count += 1
                    continue

                try:
                    stat = file_path.stat()
                    size_bytes = stat.st_size
                except (OSError, PermissionError) as e:
                    warnings.append(f"Unable to read file status: {rel_file} ({e})")
                    continue

                ext = file_path.suffix
                language = detect_language(ext, f)
                binary = is_binary_file(file_path, ext)
                category = FileCategory.OTHER if binary else classify_file(rel_file, ext, language)

                line_count = 0
                if not binary and size_bytes <= MAX_LINE_COUNT_SIZE:
                    try:
                        with open(file_path, encoding="utf-8", errors="replace") as fh:
                            line_count = sum(1 for _ in fh)
                    except Exception as e:
                        warnings.append(f"Could not count lines in {rel_file}: {e}")

                record = FileRecord(
                    rel_path=rel_file,
                    extension=ext,
                    language=language,
                    category=category,
                    size_bytes=size_bytes,
                    line_count=line_count,
                    is_binary=binary,
                )
                file_records.append(record)

                category_counts[category] += 1
                total_lines += line_count

                if language != "Unknown":
                    lang_file_counts[language] += 1
                    lang_line_counts[language] += line_count

        # Compute language stats
        total_lang_lines = sum(lang_line_counts.values()) or 1
        language_stats: list[LanguageStats] = []
        for lang, count in sorted(lang_file_counts.items(), key=lambda item: -item[1]):
            lines = lang_line_counts[lang]
            pct = round((lines / total_lang_lines) * 100, 1)
            language_stats.append(
                LanguageStats(
                    language=lang,
                    file_count=count,
                    line_count=lines,
                    percentage=pct,
                )
            )

        # Primary language heuristic: most source lines among known source languages
        source_langs = [
            stat for stat in language_stats if stat.language not in {"Markdown", "JSON", "YAML", "TOML", "Text", "Config"}
        ]
        if source_langs:
            primary_language = source_langs[0].language
        elif language_stats:
            primary_language = language_stats[0].language
        else:
            primary_language = "None"

        summary = ScanSummary(
            root_path=str(self.root_path),
            project_name=project_name,
            is_git=is_git,
            total_files=len(file_records),
            source_files=category_counts[FileCategory.SOURCE],
            test_files=category_counts[FileCategory.TEST],
            doc_files=category_counts[FileCategory.DOCUMENTATION],
            config_files=category_counts[FileCategory.CONFIGURATION],
            total_lines=total_lines,
            primary_language=primary_language,
            languages=language_stats,
            ignored_count=ignored_count,
            warnings=warnings,
        )

        return RepositoryScanResult(summary=summary, files=file_records)
