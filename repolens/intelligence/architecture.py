"""Architecture inference engine.

Infers repository architectural layers using deterministic signals: directory patterns,
framework imports, and dependency caller relationships. Always provides supporting evidence.
"""

from __future__ import annotations

from pathlib import Path

from repolens.discovery.language import is_auxiliary_path, is_sample_or_fixture_path
from repolens.models import (
    ArchitecturalLayer,
    Confidence,
    DependencyGraph,
    FileCategory,
    FileRecord,
    ModuleAnalysis,
)

LAYER_RULES = [
    {
        "name": "CLI / Interface",
        "dirs": {"cli", "cmd", "commands"},
        "files": {"cli.py", "main.py"},
        "frameworks": {"click", "typer", "argparse", "commander"},
    },
    {
        "name": "API / Web Layer",
        "dirs": {"api", "routes", "controllers", "endpoints", "views"},
        "files": {"server.py", "app.py", "router.py"},
        "frameworks": {"fastapi", "flask", "django", "express", "starlette", "aiohttp"},
    },
    {
        "name": "Services / Business Logic",
        "dirs": {"services", "service", "domain", "logic", "core"},
        "files": {"service.py", "manager.py", "handler.py"},
        "frameworks": set(),
    },
    {
        "name": "Data Access / Storage",
        "dirs": {"db", "database", "models", "repository", "repositories", "storage", "schemas"},
        "files": {"database.py", "models.py", "schema.py", "repository.py"},
        "frameworks": {"sqlite3", "sqlalchemy", "peewee", "psycopg2", "prisma", "mongoose"},
    },
    {
        "name": "Utilities / Shared",
        "dirs": {"utils", "util", "helpers", "common", "shared", "lib"},
        "files": {"utils.py", "helpers.py", "common.py"},
        "frameworks": set(),
    },
    {
        "name": "Configuration",
        "dirs": {"config", "configs", "settings"},
        "files": {"config.py", "settings.py", "constants.py", "pyproject.toml", "package.json"},
        "frameworks": {"dotenv", "pydantic_settings"},
    },
    {
        "name": "Tests",
        "dirs": {"tests", "test", "spec", "specs", "__tests__"},
        "files": set(),
        "frameworks": {"pytest", "unittest", "jest", "mocha"},
    },
]


class ArchitectureInferer:
    """Infers likely architectural layers backed by concrete repository evidence."""

    def __init__(
        self,
        files: list[FileRecord],
        analyses: dict[str, ModuleAnalysis],
        graph: DependencyGraph,
    ) -> None:
        self.files = files
        self.analyses = analyses
        self.graph = graph

    def infer(self) -> list[ArchitecturalLayer]:
        """Analyzes repository and returns inferred layers."""
        layer_results: list[ArchitecturalLayer] = []

        for rule in LAYER_RULES:
            rule_name = str(rule["name"])
            rule_dirs: set[str] = set(rule["dirs"])
            rule_files: set[str] = set(rule["files"])
            rule_frameworks: set[str] = set(rule["frameworks"])

            matched_files: list[str] = []
            evidence_points: list[str] = []

            # 1. Match files by directory or filename
            for f in self.files:
                if rule_name != "Tests" and is_auxiliary_path(f.rel_path):
                    continue
                if rule_name == "Tests" and is_sample_or_fixture_path(f.rel_path):
                    continue

                parts = set(Path(f.rel_path).parts[:-1])
                filename = Path(f.rel_path).name.lower()

                dir_match = bool(parts & rule_dirs)
                file_match = filename in rule_files

                if dir_match:
                    matched_files.append(f.rel_path)
                    evidence_points.append(f"Directory matches '{Path(f.rel_path).parent.as_posix()}' pattern.")
                elif file_match:
                    matched_files.append(f.rel_path)
                    evidence_points.append(f"Filename matches standard '{filename}' convention.")

            # 2. Match framework imports
            if rule_frameworks:
                for rel_path, analysis in self.analyses.items():
                    if rule_name != "Tests" and is_auxiliary_path(rel_path):
                        continue
                    if rule_name == "Tests" and is_sample_or_fixture_path(rel_path):
                        continue
                    for imp in analysis.imports:
                        top_pkg = imp.module.split(".")[0].lower()
                        if top_pkg in rule_frameworks:
                            if rel_path not in matched_files:
                                matched_files.append(rel_path)
                            evidence_points.append(f"Imports framework '{top_pkg}' in {rel_path}.")

            # 3. Categorize tests specifically
            if rule_name == "Tests":
                for f in self.files:
                    if is_sample_or_fixture_path(f.rel_path):
                        continue
                    if f.category == FileCategory.TEST and f.rel_path not in matched_files:
                        matched_files.append(f.rel_path)
                        evidence_points.append(f"Classified test file: {f.rel_path}")

            if matched_files:
                unique_files = sorted(set(matched_files))
                unique_evidence = sorted(set(evidence_points))[:5]  # Keep top 5 evidence points

                # Confidence heuristic
                has_framework = any("Imports framework" in e for e in unique_evidence)
                has_dir = any("Directory matches" in e for e in unique_evidence)
                if has_framework and has_dir:
                    confidence = Confidence.HIGH
                elif has_framework or has_dir or len(unique_files) >= 2:
                    confidence = Confidence.MEDIUM
                else:
                    confidence = Confidence.LOW

                layer_results.append(
                    ArchitecturalLayer(
                        layer_name=rule_name,
                        confidence=confidence,
                        files=unique_files,
                        evidence=unique_evidence,
                    )
                )

        return layer_results
