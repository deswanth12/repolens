"""Tests for the Architecture Inference engine."""

from repolens.intelligence.architecture import ArchitectureInferer
from repolens.models import (
    DependencyGraph,
    FileCategory,
    FileRecord,
    ImportRecord,
    ModuleAnalysis,
)


def test_architecture_inference():
    files = [
        FileRecord("app/cli.py", ".py", "Python", FileCategory.SOURCE, 100),
        FileRecord("app/api/routes.py", ".py", "Python", FileCategory.SOURCE, 200),
        FileRecord("app/models.py", ".py", "Python", FileCategory.SOURCE, 150),
        FileRecord("tests/test_api.py", ".py", "Python", FileCategory.TEST, 120),
    ]

    analyses = {
        "app/cli.py": ModuleAnalysis(
            rel_path="app/cli.py",
            language="Python",
            imports=[ImportRecord(module="click", is_from=False)],
        ),
        "app/api/routes.py": ModuleAnalysis(
            rel_path="app/api/routes.py",
            language="Python",
            imports=[ImportRecord(module="fastapi", is_from=False)],
        ),
        "app/models.py": ModuleAnalysis(
            rel_path="app/models.py",
            language="Python",
            imports=[ImportRecord(module="sqlalchemy", is_from=False)],
        ),
        "tests/test_api.py": ModuleAnalysis(
            rel_path="tests/test_api.py",
            language="Python",
            imports=[ImportRecord(module="pytest", is_from=False)],
        ),
    }

    graph = DependencyGraph()
    inferer = ArchitectureInferer(files, analyses, graph)
    layers = inferer.infer()

    layer_names = {l.layer_name for l in layers}
    assert "CLI / Interface" in layer_names
    assert "API / Web Layer" in layer_names
    assert "Data Access / Storage" in layer_names
    assert "Tests" in layer_names

    # Check evidence citation
    api_layer = next(l for l in layers if l.layer_name == "API / Web Layer")
    assert any("fastapi" in e for e in api_layer.evidence)
