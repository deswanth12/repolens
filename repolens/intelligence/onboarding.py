"""Contributor onboarding engine.

Builds a structured, time-boxed "Your First 30 Minutes" onboarding plan tailored
specifically to the repository, explaining what a new contributor should understand at each step.
"""

from __future__ import annotations

from pathlib import Path
from repolens.models import (
    ArchitecturalLayer,
    EntryPointRecord,
    FileCategory,
    FileRecord,
    HotspotRecord,
    OnboardingPhase,
    OnboardingPlan,
    ReadingOrderItem,
)


class OnboardingPlanner:
    """Creates a time-boxed 30-minute contributor onboarding blueprint."""

    def __init__(
        self,
        project_name: str,
        files: list[FileRecord],
        entry_points: list[EntryPointRecord],
        hotspots: list[HotspotRecord],
        layers: list[ArchitecturalLayer],
        reading_order: list[ReadingOrderItem],
    ) -> None:
        self.project_name = project_name
        self.files = files
        self.entry_points = entry_points
        self.hotspots = hotspots
        self.layers = layers
        self.reading_order = reading_order

    def plan(self) -> OnboardingPlan:
        """Generates the onboarding plan with 6 structured phases."""
        phases: list[OnboardingPhase] = []

        # Phase 1: 0-3 min (Documentation)
        doc_files = [
            f.rel_path
            for f in self.files
            if Path(f.rel_path).name.lower().startswith(("readme", "contributing"))
        ][:2]
        if not doc_files:
            doc_files = [f.rel_path for f in self.files if f.category == FileCategory.DOCUMENTATION][:1]
        phases.append(
            OnboardingPhase(
                time_window="0-3 min",
                focus="Project Vision & Problem Statement",
                target_files=doc_files or ["(No documentation files detected)"],
                takeaway="Understand why this project exists, who uses it, and its primary value proposition.",
            )
        )

        # Phase 2: 3-7 min (Entry Points)
        ep_files = [ep.rel_path for ep in self.entry_points[:2]]
        phases.append(
            OnboardingPhase(
                time_window="3-7 min",
                focus="Application Entry Point & Bootstrap",
                target_files=ep_files or ["(No explicit entry point detected)"],
                takeaway="Understand where execution starts, how arguments or configurations are parsed, and how the core coordinator is initialized.",
            )
        )

        # Phase 3: 7-15 min (Core Workflow & Orchestration)
        core_files = [hs.rel_path for hs in self.hotspots if hs.rel_path not in ep_files][:2]
        if not core_files:
            core_files = [item.rel_path for item in self.reading_order if item.category == "Core Component"][:2]
        phases.append(
            OnboardingPhase(
                time_window="7-15 min",
                focus="Core Workflow & Orchestration",
                target_files=core_files or ["(No central orchestrator detected)"],
                takeaway="Understand the primary execution lifecycle, how data enters the pipeline, and how tasks are coordinated.",
            )
        )

        # Phase 4: 15-22 min (Domain Models & Entities)
        model_layer = next((l for l in self.layers if "Data" in l.layer_name or "Models" in l.layer_name), None)
        model_files = [f for f in (model_layer.files if model_layer else []) if not any(x in f for x in ("fixtures", "__pycache__"))][:2]
        if not model_files:
            model_files = [
                f.rel_path
                for f in self.files
                if f.category == FileCategory.SOURCE
                and not any(x in f.rel_path for x in ("fixtures", "__pycache__"))
                and any(m in Path(f.rel_path).name.lower() for m in ("model", "schema", "type"))
            ][:2]
        phases.append(
            OnboardingPhase(
                time_window="15-22 min",
                focus="Domain Models & Core Entities",
                target_files=model_files or ["(Models defined within core modules)"],
                takeaway="Understand the primary data representations, contracts, and internal state structures.",
            )
        )

        # Phase 5: 22-27 min (Supporting Infrastructure & Utilities)
        util_layer = next((l for l in self.layers if "Utilities" in l.layer_name), None)
        util_files = [f for f in (util_layer.files if util_layer else []) if not any(x in f for x in ("fixtures", "__pycache__"))][:2]
        if not util_files:
            util_files = [
                f.rel_path
                for f in self.files
                if f.category == FileCategory.SOURCE
                and not any(x in f.rel_path for x in ("fixtures", "__pycache__"))
                and any(m in Path(f.rel_path).name.lower() for m in ("util", "helper", "ignore", "config", "resolver", "scanner"))
            ][:2]
        phases.append(
            OnboardingPhase(
                time_window="22-27 min",
                focus="Supporting Infrastructure & Utilities",
                target_files=util_files or ["(No dedicated utility layer detected)"],
                takeaway="Understand foundational helper logic, external service adapters, and configuration loaders.",
            )
        )

        # Phase 6: 27-30 min (Tests & Verification)
        test_files = [
            f.rel_path
            for f in self.files
            if f.category == FileCategory.TEST
            and not any(x in f.rel_path for x in ("fixtures", "__pycache__"))
        ][:2]
        phases.append(
            OnboardingPhase(
                time_window="27-30 min",
                focus="Test Contracts & Behavior Verification",
                target_files=test_files or ["(No test suite detected)"],
                takeaway="Understand how behaviors are verified, how to run tests locally, and how to write a test before opening a PR.",
            )
        )

        summary_notes = [
            f"Repository '{self.project_name}' contains {len(self.files)} files.",
            f"Identified {len(self.entry_points)} application entry point candidates.",
            f"Identified {len(self.hotspots)} high-connectivity structural modules.",
        ]

        return OnboardingPlan(
            project_name=self.project_name,
            phases=phases,
            summary_notes=summary_notes,
        )
