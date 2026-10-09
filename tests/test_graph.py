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


def test_import_resolver_js_relative_and_aliases():
    known_paths = {
        "src/App.jsx",
        "src/components/Button.jsx",
        "src/components/Header/index.tsx",
        "src/utils/api.ts",
    }
    resolver = ImportResolver(known_paths)

    # Relative import from src/App.jsx to ./components/Button
    imp1 = ImportRecord(module="./components/Button", is_from=True, level=1)
    target1, is_int1 = resolver.resolve("src/App.jsx", imp1)
    assert is_int1 is True
    assert target1 == "src/components/Button.jsx"

    # Relative import from src/components/Button.jsx to ../utils/api
    imp2 = ImportRecord(module="../utils/api", is_from=True, level=2)
    target2, is_int2 = resolver.resolve("src/components/Button.jsx", imp2)
    assert is_int2 is True
    assert target2 == "src/utils/api.ts"

    # Index resolution: import from ./Header resolves to src/components/Header/index.tsx
    imp3 = ImportRecord(module="./Header", is_from=True, level=1)
    target3, is_int3 = resolver.resolve("src/components/Button.jsx", imp3)
    assert is_int3 is True
    assert target3 == "src/components/Header/index.tsx"

    # Path alias resolution: '@/utils/api' or '~/components/Button'
    imp4 = ImportRecord(module="@/utils/api", is_from=True, level=0)
    target4, is_int4 = resolver.resolve("src/App.jsx", imp4)
    assert is_int4 is True
    assert target4 == "src/utils/api.ts"
