"""Reading order generation engine.

Produces a sequential, evidence-based reading roadmap designed to help a developer
build an accurate mental model of an unfamiliar codebase in minimum time.
"""

from __future__ import annotations

from pathlib import Path
from repolens.models import (
    EntryPointRecord,
    FileCategory,
    FileRecord,
    HotspotRecord,
    ReadingOrderItem,
)


class ReadingOrderEngine:
    """Generates an optimal reading order for unfamiliar codebases."""

    def __init__(
        self,
        files: list[FileRecord],
        entry_points: list[EntryPointRecord],
        hotspots: list[HotspotRecord],
    ) -> None:
        self.files = files
        self.entry_points = entry_points
        self.hotspots = hotspots

    def generate(self) -> list[ReadingOrderItem]:
        """Calculates prioritized reading order steps."""
        items: list[ReadingOrderItem] = []
        selected_paths: set[str] = set()

        def add_item(rel_path: str, category: str, purpose: str) -> None:
            if rel_path in selected_paths:
                return
            selected_paths.add(rel_path)
            items.append(
                ReadingOrderItem(
                    order=len(items) + 1,
                    rel_path=rel_path,
                    category=category,
                    purpose=purpose,
                )
            )

        # 1. Primary Documentation (README)
        readme = next(
            (f.rel_path for f in self.files if Path(f.rel_path).name.lower().startswith("readme")),
            None,
        )
        if readme:
            add_item(
                readme,
                "Documentation",
                "Understand the project's purpose, scope, and user-facing design.",
            )

        # 2. Project Manifest (pyproject.toml / package.json)
        manifest = next(
            (
                f.rel_path
                for f in self.files
                if Path(f.rel_path).name.lower() in {"pyproject.toml", "package.json", "setup.py", "cargo.toml"}
            ),
            None,
        )
        if manifest:
            add_item(
                manifest,
                "Configuration",
                "Inspect declared dependencies, build configuration, and runnable entry points.",
            )

        # 3. Primary Application Entry Point
        if self.entry_points:
            top_ep = self.entry_points[0]
            add_item(
                top_ep.rel_path,
                "Entry Point",
                f"Application starting point ({top_ep.category}); trace execution kickoff and wiring.",
            )

        # 4. Top Structural Hotspots / Orchestrators
        for hs in self.hotspots:
            if hs.rel_path not in selected_paths:
                purpose = hs.interpretation or "Central module with high structural connectivity."
                add_item(
                    hs.rel_path,
                    "Core Component",
                    purpose,
                )
                if len(items) >= 5:
                    break

        # 5. Core Data Models / Entities
        model_file = next(
            (
                f.rel_path
                for f in self.files
                if f.category == FileCategory.SOURCE
                and any(m in Path(f.rel_path).name.lower() for m in ("model", "schema", "types", "entity"))
                and f.rel_path not in selected_paths
            ),
            None,
        )
        if model_file:
            add_item(
                model_file,
                "Domain Model",
                "Core domain representations, data models, and typed contracts.",
            )

        # 6. Canonical Test Suite
        test_file = next(
            (
                f.rel_path
                for f in self.files
                if f.category == FileCategory.TEST and f.rel_path not in selected_paths
            ),
            None,
        )
        if test_file:
            add_item(
                test_file,
                "Verification",
                "Observe expected inputs, outputs, error conditions, and test contracts.",
            )

        return items
