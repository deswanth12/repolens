"""Hotspot detection engine.

Identifies structurally important and central modules based on measurable graph connectivity
and symbol density. Treats connectivity as structural significance, not defect scoring.
"""

from __future__ import annotations

from repolens.models import DependencyGraph, HotspotRecord, ModuleAnalysis


class HotspotDetector:
    """Detects architectural hubs and structural hotspots."""

    def __init__(
        self,
        graph: DependencyGraph,
        analyses: dict[str, ModuleAnalysis],
    ) -> None:
        self.graph = graph
        self.analyses = analyses

    def detect(self) -> list[HotspotRecord]:
        """Calculates hotspot rankings with explainable rationales."""
        records: list[HotspotRecord] = []

        for rel_path, node in self.graph.nodes.items():
            dep_in = node.dependent_count
            dep_out = node.dependency_count
            symbols = node.symbol_count
            connectivity = node.connectivity

            # Require minimum connectivity or significant symbol density
            if connectivity < 1 and symbols < 5:
                continue

            reasons: list[str] = []
            if dep_in > 0:
                s_plural = "s" if dep_in > 1 else ""
                reasons.append(f"{dep_in} internal module{s_plural} depend on this file.")
            if dep_out > 0:
                s_plural = "s" if dep_out > 1 else ""
                reasons.append(f"Imports {dep_out} internal module{s_plural}.")
            if symbols > 0:
                s_plural = "s" if symbols > 1 else ""
                reasons.append(f"Defines {symbols} symbols (functions/classes).")

            # Explainable interpretation
            if dep_in >= 3 and dep_out <= 2:
                interpretation = (
                    "Foundational module: heavily relied upon by other modules with minimal outgoing dependencies."
                )
            elif dep_in >= 2 and dep_out >= 2:
                interpretation = (
                    "Structural nexus: high two-way connectivity; acts as a central coordination point."
                )
            elif dep_out >= 3:
                interpretation = (
                    "Orchestrator: aggregates multiple internal subsystems."
                )
            elif dep_in >= 1:
                interpretation = (
                    "Shared component: imported by downstream modules."
                )
            else:
                interpretation = (
                    "Dense module: contains significant symbol concentration."
                )

            records.append(
                HotspotRecord(
                    rel_path=rel_path,
                    dependent_count=dep_in,
                    dependency_count=dep_out,
                    symbol_count=symbols,
                    connectivity=connectivity,
                    reasons=reasons,
                    interpretation=interpretation,
                )
            )

        # Sort by connectivity (descending), then in-degree (descending), then symbol count
        records.sort(
            key=lambda r: (r.connectivity, r.dependent_count, r.symbol_count),
            reverse=True,
        )

        return records
