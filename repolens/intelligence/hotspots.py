"""Hotspot detection engine.

Identifies structurally important and central modules based on measurable graph connectivity
and symbol density. Treats connectivity as structural significance, not defect scoring.
"""

from __future__ import annotations

from repolens.models import DependencyGraph, HotspotRecord, ModuleAnalysis


def _is_test_file(path: str) -> bool:
    lower_rel = path.lower().replace("\\", "/")
    parts = lower_rel.split("/")
    if any(p in {"tests", "test", "fixtures", "spec", "specs", "__tests__"} for p in parts[:-1]):
        return True
    filename = parts[-1]
    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or filename.endswith(".test.js")
        or filename.endswith(".spec.ts")
        or filename.endswith(".test.ts")
    )


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
            if _is_test_file(rel_path):
                continue

            # Separate production callers from test callers
            prod_dependents = [d for d in node.dependents if not _is_test_file(d)]
            test_dependents = [d for d in node.dependents if _is_test_file(d)]
            prod_in = len(prod_dependents)
            test_in = len(test_dependents)

            dep_in = node.dependent_count
            dep_out = node.dependency_count
            symbols = node.symbol_count
            connectivity = node.connectivity

            # Require minimum connectivity or significant symbol density
            if connectivity < 1 and symbols < 5:
                continue

            reasons: list[str] = []
            if test_in > 0 and prod_in > 0:
                s_plural = "s" if prod_in > 1 else ""
                t_plural = "s" if test_in > 1 else ""
                reasons.append(
                    f"{prod_in} internal module{s_plural} depend on this file (+{test_in} test suite{t_plural})."
                )
            elif prod_in > 0:
                s_plural = "s" if prod_in > 1 else ""
                reasons.append(f"{prod_in} internal module{s_plural} depend on this file.")
            elif test_in > 0:
                t_plural = "s" if test_in > 1 else ""
                reasons.append(f"Imported by {test_in} test suite{t_plural} (0 internal source callers).")

            if dep_out > 0:
                s_plural = "s" if dep_out > 1 else ""
                reasons.append(f"Imports {dep_out} internal module{s_plural}.")
            if symbols > 0:
                s_plural = "s" if symbols > 1 else ""
                reasons.append(f"Defines {symbols} symbols (functions/classes).")

            # Explainable interpretation based primarily on production architecture
            if prod_in >= 3 and dep_out <= 2:
                interpretation = (
                    "Foundational module: heavily relied upon by other modules with minimal outgoing dependencies."
                )
            elif prod_in >= 2 and dep_out >= 2:
                interpretation = (
                    "Structural nexus: high two-way connectivity; acts as a central coordination point."
                )
            elif dep_out >= 3:
                interpretation = (
                    "Orchestrator: aggregates multiple internal subsystems."
                )
            elif prod_in >= 1:
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

        # Sort by production connectivity first to prioritize architectural cores, then raw connectivity, then symbols
        def _sort_key(r: HotspotRecord) -> tuple[int, int, int]:
            # Estimate prod callers: if reason has prod callers, or fallback to dependent_count
            return (r.connectivity, r.dependent_count, r.symbol_count)

        records.sort(key=_sort_key, reverse=True)

        return records
