"""Entry point detection engine.

Identifies application entry points using deterministic AST markers,
packaging manifests (pyproject.toml, package.json), and structural heuristics.
Always includes evidence and confidence ratings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    tomllib = None  # type: ignore

from repolens.models import Confidence, EntryPointRecord, ModuleAnalysis

ENTRYPOINT_FILENAMES = {
    "main.py": ("Application", "Standard Python application entry-point filename"),
    "cli.py": ("CLI", "Standard command-line interface entry-point filename"),
    "app.py": ("Web / Application", "Standard application server entry-point filename"),
    "server.py": ("Server", "Standard backend server entry-point filename"),
    "manage.py": ("CLI / Framework", "Django management script entry point"),
    "wsgi.py": ("Web Server", "WSGI application gateway entry point"),
    "asgi.py": ("Web Server", "ASGI asynchronous application gateway entry point"),
    "index.js": ("Application", "Standard JavaScript module entry point"),
    "index.ts": ("Application", "Standard TypeScript module entry point"),
    "server.js": ("Server", "Node.js server entry point"),
    "server.ts": ("Server", "TypeScript server entry point"),
}

CLI_DECORATOR_MARKERS = {"click.command", "click.group", "command", "group"}


class EntryPointDetector:
    """Detects likely application entry points across repository modules."""

    def __init__(
        self,
        repo_root: Path,
        analyses: dict[str, ModuleAnalysis],
    ) -> None:
        self.repo_root = repo_root
        self.analyses = analyses

    def detect(self) -> list[EntryPointRecord]:
        """Runs detection and returns ranked list of entry points."""
        # Map of rel_path -> EntryPointRecord builder
        records_map: dict[str, dict[str, Any]] = {}

        def get_or_create(rel_path: str) -> dict[str, Any]:
            if rel_path not in records_map:
                records_map[rel_path] = {
                    "rel_path": rel_path,
                    "reasons": [],
                    "confidence": Confidence.LOW,
                    "category": "Application",
                }
            return records_map[rel_path]

        # 1. Inspect pyproject.toml scripts
        self._inspect_pyproject(get_or_create)

        # 2. Inspect package.json scripts / bin
        self._inspect_package_json(get_or_create)

        # 3. Inspect module AST analysis
        for rel_path, analysis in self.analyses.items():
            entry = get_or_create(rel_path)
            file_name = Path(rel_path).name.lower()

            # Signal A: Contains __main__ guard
            if analysis.has_main_block:
                entry["reasons"].append("Contains '__main__' execution block.")
                entry["confidence"] = Confidence.HIGH

            # Signal B: CLI decorators or command functions
            has_cli_decorator = False
            for symbol in analysis.symbols:
                for dec in symbol.decorators:
                    if any(marker in dec.lower() for marker in CLI_DECORATOR_MARKERS):
                        has_cli_decorator = True
                        break
                if symbol.name.lower() in {"main", "cli", "run"} and symbol.parent_symbol is None:
                    entry["reasons"].append(f"Defines top-level '{symbol.name}()' execution function.")
                    if entry["confidence"] != Confidence.HIGH:
                        entry["confidence"] = Confidence.MEDIUM

            if has_cli_decorator:
                entry["reasons"].append("Defines CLI command decorators (e.g., Click/Typer).")
                entry["category"] = "CLI"
                entry["confidence"] = Confidence.HIGH

            # Signal C: Entrypoint filename conventions
            if file_name in ENTRYPOINT_FILENAMES:
                cat, reason = ENTRYPOINT_FILENAMES[file_name]
                entry["reasons"].append(f"{reason} ({file_name}).")
                if entry["category"] == "Application":
                    entry["category"] = cat
                if entry["confidence"] == Confidence.LOW:
                    entry["confidence"] = Confidence.MEDIUM

        # Convert to EntryPointRecord objects
        results: list[EntryPointRecord] = []
        for rel_path, data in records_map.items():
            if data["reasons"]:  # Only include if at least one evidence signal exists
                results.append(
                    EntryPointRecord(
                        rel_path=rel_path,
                        reasons=data["reasons"],
                        confidence=data["confidence"],
                        category=data["category"],
                    )
                )

        # Rank by confidence: HIGH first, then MEDIUM, then LOW
        confidence_rank = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
        results.sort(key=lambda r: (confidence_rank[r.confidence], len(r.rel_path)))

        return results

    def _inspect_pyproject(self, get_or_create_fn: Any) -> None:
        """Parses pyproject.toml for script definitions."""
        pyproject_file = self.repo_root / "pyproject.toml"
        if not pyproject_file.is_file() or tomllib is None:
            return

        try:
            content = pyproject_file.read_text(encoding="utf-8", errors="replace")
            data = tomllib.loads(content)
        except Exception:
            return

        # Look in [project.scripts] and [tool.poetry.scripts]
        scripts: dict[str, str] = {}
        project = data.get("project", {})
        if "scripts" in project and isinstance(project["scripts"], dict):
            scripts.update(project["scripts"])

        poetry = data.get("tool", {}).get("poetry", {})
        if "scripts" in poetry and isinstance(poetry["scripts"], dict):
            scripts.update(poetry["scripts"])

        for cmd_name, entry_str in scripts.items():
            # e.g. "repolens.cli:main" -> "repolens/cli"
            mod_part = entry_str.split(":")[0].strip()
            expected_stem = mod_part.replace(".", "/")

            # Match against known analyzed paths
            for rel_path in self.analyses:
                stem = rel_path.rsplit(".", 1)[0]
                if stem == expected_stem or stem == f"src/{expected_stem}":
                    entry = get_or_create_fn(rel_path)
                    entry["reasons"].append(
                        f"Configured as executable console script '{cmd_name}' in pyproject.toml."
                    )
                    entry["confidence"] = Confidence.HIGH
                    entry["category"] = "CLI / Script"

    def _inspect_package_json(self, get_or_create_fn: Any) -> None:
        """Parses package.json for bin and scripts."""
        pkg_file = self.repo_root / "package.json"
        if not pkg_file.is_file():
            return

        try:
            content = pkg_file.read_text(encoding="utf-8", errors="replace")
            data = json.loads(content)
        except Exception:
            return

        # bin field: string or dict
        bins = data.get("bin", {})
        bin_paths: list[str] = []
        if isinstance(bins, str):
            bin_paths.append(bins)
        elif isinstance(bins, dict):
            bin_paths.extend(bins.values())

        for bp in bin_paths:
            norm_bp = bp.lstrip("./").replace("\\", "/")
            for rel_path in self.analyses:
                if rel_path == norm_bp:
                    entry = get_or_create_fn(rel_path)
                    entry["reasons"].append("Configured in package.json 'bin' field.")
                    entry["confidence"] = Confidence.HIGH
                    entry["category"] = "CLI / Binary"
