"""Tests for the Hotspot Detection engine."""

from repolens.intelligence.hotspots import HotspotDetector
from repolens.models import DependencyGraph, ModuleAnalysis, ModuleNode


def test_hotspot_detection():
    # Setup graph where central.py is imported by 3 modules and imports 1 module
    nodes = {
        "app/central.py": ModuleNode(
            rel_path="app/central.py",
            language="Python",
            dependencies=["app/db.py"],
            dependents=["app/api.py", "app/cli.py", "app/worker.py"],
            symbol_count=15,
        ),
        "app/db.py": ModuleNode(
            rel_path="app/db.py",
            language="Python",
            dependencies=[],
            dependents=["app/central.py"],
            symbol_count=4,
        ),
        "app/leaf.py": ModuleNode(
            rel_path="app/leaf.py",
            language="Python",
            dependencies=[],
            dependents=[],
            symbol_count=1,
        ),
    }

    graph = DependencyGraph(nodes=nodes)
    analyses = {
        k: ModuleAnalysis(rel_path=k, language="Python", symbols=[]) for k in nodes
    }

    detector = HotspotDetector(graph, analyses)
    hotspots = detector.detect()

    # central.py should be top hotspot
    assert len(hotspots) >= 1
    assert hotspots[0].rel_path == "app/central.py"
    assert hotspots[0].dependent_count == 3
    assert hotspots[0].dependency_count == 1
    assert hotspots[0].connectivity == 4
    assert any("3 internal modules" in r for r in hotspots[0].reasons)
    assert "Foundational" in hotspots[0].interpretation or "nexus" in hotspots[0].interpretation.lower()
