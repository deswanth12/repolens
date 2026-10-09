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

    layer_names = {layer.layer_name for layer in layers}
    assert "CLI / Interface" in layer_names
    assert "API / Web Layer" in layer_names
    assert "Data Access / Storage" in layer_names
    assert "Tests" in layer_names

    # Check evidence citation
    api_layer = next(layer for layer in layers if layer.layer_name == "API / Web Layer")
    assert any("fastapi" in e for e in api_layer.evidence)


def test_architecture_inference_excludes_samples_and_fixtures():
    files = [
        FileRecord("app/cli.py", ".py", "Python", FileCategory.SOURCE, 100),
        FileRecord("samples/demo/app/api/routes.py", ".py", "Python", FileCategory.SOURCE, 200),
        FileRecord("tests/fixtures/test_fix/routes.py", ".py", "Python", FileCategory.SOURCE, 200),
        FileRecord("tests/test_cli.py", ".py", "Python", FileCategory.TEST, 120),
        FileRecord("samples/demo/tests/test_demo.py", ".py", "Python", FileCategory.TEST, 80),
    ]

    analyses = {
        "app/cli.py": ModuleAnalysis(
            rel_path="app/cli.py",
            language="Python",
            imports=[ImportRecord(module="click", is_from=False)],
        ),
        "samples/demo/app/api/routes.py": ModuleAnalysis(
            rel_path="samples/demo/app/api/routes.py",
            language="Python",
            imports=[ImportRecord(module="fastapi", is_from=False)],
        ),
        "tests/fixtures/test_fix/routes.py": ModuleAnalysis(
            rel_path="tests/fixtures/test_fix/routes.py",
            language="Python",
            imports=[ImportRecord(module="fastapi", is_from=False)],
        ),
        "tests/test_cli.py": ModuleAnalysis(
            rel_path="tests/test_cli.py",
            language="Python",
            imports=[ImportRecord(module="pytest", is_from=False)],
        ),
        "samples/demo/tests/test_demo.py": ModuleAnalysis(
            rel_path="samples/demo/tests/test_demo.py",
            language="Python",
            imports=[ImportRecord(module="pytest", is_from=False)],
        ),
    }

    graph = DependencyGraph()
    inferer = ArchitectureInferer(files, analyses, graph)
    layers = inferer.infer()

    layer_names = {layer.layer_name for layer in layers}
    # CLI and Tests should exist; API layer from samples/fixtures should NOT
    assert "CLI / Interface" in layer_names
    assert "Tests" in layer_names
    assert "API / Web Layer" not in layer_names

    tests_layer = next(layer for layer in layers if layer.layer_name == "Tests")
    assert "tests/test_cli.py" in tests_layer.files
    assert all("samples/" not in f for f in tests_layer.files)

