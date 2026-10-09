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


def test_hotspot_distinguishes_tests_and_source():
    nodes = {
        "app/models.py": ModuleNode(
            rel_path="app/models.py",
            language="Python",
            dependencies=[],
            dependents=[
                "app/service.py",
                "tests/test_one.py",
                "tests/test_two.py",
            ],
            symbol_count=10,
        ),
        "app/service.py": ModuleNode(
            rel_path="app/service.py",
            language="Python",
            dependencies=["app/models.py"],
            dependents=[],
            symbol_count=5,
        ),
        "tests/test_one.py": ModuleNode(
            rel_path="tests/test_one.py",
            language="Python",
            dependencies=["app/models.py"],
            dependents=[],
            symbol_count=2,
        ),
        "tests/test_two.py": ModuleNode(
            rel_path="tests/test_two.py",
            language="Python",
            dependencies=["app/models.py"],
            dependents=[],
            symbol_count=2,
        ),
    }

    graph = DependencyGraph(nodes=nodes)
    analyses = {k: ModuleAnalysis(rel_path=k, language="Python", symbols=[]) for k in nodes}

    detector = HotspotDetector(graph, analyses)
    hotspots = detector.detect()

    # Test files themselves must not be listed as hotspots
    assert all("tests/" not in h.rel_path for h in hotspots)

    models_spot = next(h for h in hotspots if h.rel_path == "app/models.py")
    # Must report 1 internal module + 2 test suites
    assert any("1 internal module depend" in r and "2 test suites" in r for r in models_spot.reasons)
