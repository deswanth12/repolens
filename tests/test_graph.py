"""Tests for dependency graph builder, resolver, and cycle detection."""

from repolens.graph.builder import DependencyGraphBuilder, find_cycles
from repolens.graph.resolver import ImportResolver
from repolens.models import ImportRecord, ModuleAnalysis


def test_import_resolver():
    known_paths = {
        "pkg/main.py",
        "pkg/utils.py",
        "pkg/db/__init__.py",
        "pkg/db/client.py",
    }
    resolver = ImportResolver(known_paths)

    # Relative import from pkg/main.py to utils
    rel_imp = ImportRecord(module="", imported_names=["utils"], is_from=True, level=1)
    target, is_internal = resolver.resolve("pkg/main.py", rel_imp)
    assert is_internal is True
    assert target == "pkg/utils.py"

    # Relative import from pkg/db/client.py to ..utils
    rel_parent = ImportRecord(module="utils", is_from=True, level=2)
    target, is_internal = resolver.resolve("pkg/db/client.py", rel_parent)
    assert is_internal is True
    assert target == "pkg/utils.py"

    # Absolute import
    abs_imp = ImportRecord(module="pkg.db.client", is_from=False, level=0)
    target, is_internal = resolver.resolve("pkg/main.py", abs_imp)
    assert is_internal is True
    assert target == "pkg/db/client.py"

    # External import
    ext_imp = ImportRecord(module="requests", is_from=False, level=0)
    target, is_internal = resolver.resolve("pkg/main.py", ext_imp)
    assert is_internal is False
    assert target == "requests"


def test_dependency_graph_builder():
    analyses = {
        "app/main.py": ModuleAnalysis(
            rel_path="app/main.py",
            language="Python",
            imports=[
                ImportRecord(module="app.service", is_from=False, level=0),
                ImportRecord(module="os", is_from=False, level=0),
            ],
        ),
        "app/service.py": ModuleAnalysis(
            rel_path="app/service.py",
            language="Python",
            imports=[
                ImportRecord(module="app.db", is_from=False, level=0),
            ],
        ),
        "app/db.py": ModuleAnalysis(
            rel_path="app/db.py",
            language="Python",
            imports=[],
        ),
    }

    builder = DependencyGraphBuilder(analyses)
    graph = builder.build()

    # app/main depends on app/service
    assert "app/service.py" in graph.nodes["app/main.py"].dependencies
    assert "os" in graph.nodes["app/main.py"].external_dependencies

    # app/service is dependent of app/main, and depends on app/db
    assert "app/main.py" in graph.nodes["app/service.py"].dependents
    assert "app/db.py" in graph.nodes["app/service.py"].dependencies

    # app/db has dependent app/service
    assert "app/service.py" in graph.nodes["app/db.py"].dependents
    assert len(graph.nodes["app/db.py"].dependencies) == 0

    # No cycles in this DAG
    assert len(graph.cycles) == 0


def test_cycle_detection():
    adj = {
        "a.py": ["b.py"],
        "b.py": ["c.py"],
        "c.py": ["a.py"],
        "d.py": ["c.py"],
    }
    cycles = find_cycles(adj)
    assert len(cycles) == 1
    # Check cycle elements
    cycle = cycles[0]
    assert cycle[0] == cycle[-1]  # Closed loop
    assert set(cycle) == {"a.py", "b.py", "c.py"}
