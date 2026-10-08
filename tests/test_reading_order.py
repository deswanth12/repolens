"""Tests for the Reading Order Generation engine."""

from repolens.intelligence.reading_order import ReadingOrderEngine
from repolens.models import (
    Confidence,
    EntryPointRecord,
    FileCategory,
    FileRecord,
    HotspotRecord,
)


def test_reading_order_generation():
    files = [
        FileRecord("README.md", ".md", "Markdown", FileCategory.DOCUMENTATION, 500),
        FileRecord("pyproject.toml", ".toml", "TOML", FileCategory.CONFIGURATION, 200),
        FileRecord("app/main.py", ".py", "Python", FileCategory.SOURCE, 300),
        FileRecord("app/core.py", ".py", "Python", FileCategory.SOURCE, 400),
        FileRecord("app/models.py", ".py", "Python", FileCategory.SOURCE, 250),
        FileRecord("tests/test_main.py", ".py", "Python", FileCategory.TEST, 150),
    ]

    entry_points = [
        EntryPointRecord(
            rel_path="app/main.py",
            reasons=["Contains __main__"],
            confidence=Confidence.HIGH,
            category="CLI",
        )
    ]

    hotspots = [
        HotspotRecord(
            rel_path="app/core.py",
            dependent_count=4,
            dependency_count=2,
            symbol_count=12,
            connectivity=6,
            interpretation="Orchestrator module.",
        )
    ]

    engine = ReadingOrderEngine(files, entry_points, hotspots)
    reading_list = engine.generate()

    # Step 1 should be README
    assert reading_list[0].rel_path == "README.md"
    assert reading_list[0].order == 1

    # Step 2 should be pyproject.toml
    assert reading_list[1].rel_path == "pyproject.toml"

    # Step 3 should be app/main.py
    assert reading_list[2].rel_path == "app/main.py"

    # Step 4 should be core.py (hotspot)
    assert reading_list[3].rel_path == "app/core.py"

    # Step 5 should be models.py (domain model)
    assert reading_list[4].rel_path == "app/models.py"

    # Test file should be included towards the end
    assert any(item.rel_path == "tests/test_main.py" for item in reading_list)
