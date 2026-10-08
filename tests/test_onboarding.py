"""Tests for the Contributor Onboarding engine."""

from repolens.intelligence.onboarding import OnboardingPlanner
from repolens.models import (
    ArchitecturalLayer,
    Confidence,
    EntryPointRecord,
    FileCategory,
    FileRecord,
    HotspotRecord,
    ReadingOrderItem,
)


def test_onboarding_plan_generation():
    files = [
        FileRecord("README.md", ".md", "Markdown", FileCategory.DOCUMENTATION, 500),
        FileRecord("app/main.py", ".py", "Python", FileCategory.SOURCE, 300),
        FileRecord("app/scanner.py", ".py", "Python", FileCategory.SOURCE, 400),
        FileRecord("app/models.py", ".py", "Python", FileCategory.SOURCE, 250),
        FileRecord("app/utils.py", ".py", "Python", FileCategory.SOURCE, 150),
        FileRecord("tests/test_scanner.py", ".py", "Python", FileCategory.TEST, 200),
    ]

    entry_points = [
        EntryPointRecord("app/main.py", ["Contains __main__"], Confidence.HIGH, "CLI")
    ]
    hotspots = [
        HotspotRecord("app/scanner.py", 3, 2, 8, 5, ["Connected"], "Orchestrator")
    ]
    layers = [
        ArchitecturalLayer("Data Access / Storage", Confidence.HIGH, ["app/models.py"], ["Convention"]),
        ArchitecturalLayer("Utilities / Shared", Confidence.HIGH, ["app/utils.py"], ["Convention"]),
    ]
    reading_order = [
        ReadingOrderItem(1, "README.md", "Documentation", "Docs"),
        ReadingOrderItem(2, "app/main.py", "Entry Point", "Main"),
    ]

    planner = OnboardingPlanner(
        project_name="TestProject",
        files=files,
        entry_points=entry_points,
        hotspots=hotspots,
        layers=layers,
        reading_order=reading_order,
    )
    plan = planner.plan()

    assert plan.project_name == "TestProject"
    assert len(plan.phases) == 6

    # Verify time windows
    time_windows = [p.time_window for p in plan.phases]
    assert time_windows == [
        "0-3 min",
        "3-7 min",
        "7-15 min",
        "15-22 min",
        "22-27 min",
        "27-30 min",
    ]

    # Check that each phase has non-empty target files and takeaway
    for phase in plan.phases:
        assert len(phase.target_files) > 0
        assert len(phase.takeaway) > 10
        assert len(phase.focus) > 0

    assert "README.md" in plan.phases[0].target_files
    assert "app/main.py" in plan.phases[1].target_files
    assert "app/scanner.py" in plan.phases[2].target_files
    assert "app/models.py" in plan.phases[3].target_files
    assert "tests/test_scanner.py" in plan.phases[5].target_files
