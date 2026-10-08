"""Dependency graph construction and cycle detection engine."""

from __future__ import annotations

from repolens.graph.resolver import ImportResolver
from repolens.models import (
    DependencyEdge,
    DependencyGraph,
    ModuleAnalysis,
    ModuleNode,
)


def find_cycles(adj: dict[str, list[str]]) -> list[list[str]]:
    """Finds directed circular dependency cycles using DFS."""
    visited: set[str] = set()
    rec_stack: list[str] = []
    rec_set: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.append(node)
        rec_set.add(node)

        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_set:
                # Cycle detected: extract subpath from neighbor to current
                cycle_start_idx = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start_idx:] + [neighbor]
                cycles.append(cycle)

        rec_stack.pop()
        rec_set.remove(node)

    for n in sorted(adj.keys()):
        if n not in visited:
            dfs(n)

    return cycles


class DependencyGraphBuilder:
    """Builds a connected dependency graph from per-module analyses."""

    def __init__(self, analyses: dict[str, ModuleAnalysis]) -> None:
        self.analyses = analyses
        self.resolver = ImportResolver(set(analyses.keys()))

    def build(self) -> DependencyGraph:
        """Constructs and returns the dependency graph."""
        nodes: dict[str, ModuleNode] = {}
        edges: list[DependencyEdge] = []

        # Initialize nodes
        for rel_path, analysis in self.analyses.items():
            nodes[rel_path] = ModuleNode(
                rel_path=rel_path,
                language=analysis.language,
                symbol_count=len(analysis.symbols),
            )

        # Populate edges and dependencies
        adj: dict[str, list[str]] = {p: [] for p in nodes}

        for source_path, analysis in self.analyses.items():
            source_node = nodes[source_path]

            for imp in analysis.imports:
                target, is_internal = self.resolver.resolve(source_path, imp)

                edge = DependencyEdge(
                    source=source_path,
                    target=target,
                    is_internal=is_internal,
                    line_number=imp.line_number,
                    imported_symbols=imp.imported_names,
                )
                edges.append(edge)

                if is_internal and target in nodes:
                    if target != source_path:
                        if target not in source_node.dependencies:
                            source_node.dependencies.append(target)
                            adj[source_path].append(target)
                        if source_path not in nodes[target].dependents:
                            nodes[target].dependents.append(source_path)
                else:
                    if target and target not in source_node.external_dependencies:
                        source_node.external_dependencies.append(target)

        # Detect cycles
        cycles = find_cycles(adj)

        # Sort dependency lists for determinism
        for node in nodes.values():
            node.dependencies.sort()
            node.dependents.sort()
            node.external_dependencies.sort()

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            cycles=cycles,
        )
