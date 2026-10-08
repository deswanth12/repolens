"""Graph formatters for Mermaid and DOT syntax."""

from __future__ import annotations

import re
from repolens.models import DependencyGraph


def _sanitize_id(name: str) -> str:
    """Converts a file path to a valid identifier for diagrams."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def to_mermaid(graph: DependencyGraph, max_edges: int = 50) -> str:
    """Renders the internal module dependency graph as a Mermaid diagram."""
    lines: list[str] = ["graph TD"]

    # Filter to internal edges only
    internal_edges = [e for e in graph.edges if e.is_internal and e.target in graph.nodes]

    if not internal_edges:
        lines.append("    Empty[\"No internal module dependencies detected\"]")
        return "\n".join(lines)

    edge_count = 0
    for edge in internal_edges:
        if edge_count >= max_edges:
            lines.append("    %% ... additional edges truncated for readability")
            break
        src_id = _sanitize_id(edge.source)
        tgt_id = _sanitize_id(edge.target)
        lines.append(f'    {src_id}["{edge.source}"] --> {tgt_id}["{edge.target}"]')
        edge_count += 1

    return "\n".join(lines)


def to_dot(graph: DependencyGraph) -> str:
    """Renders the internal module dependency graph as Graphviz DOT syntax."""
    lines: list[str] = [
        'digraph RepositoryDependencies {',
        '    node [shape=box, style=rounded, fontname="Helvetica"];',
        '    edge [color="#666666"];',
    ]

    internal_edges = [e for e in graph.edges if e.is_internal and e.target in graph.nodes]
    if not internal_edges:
        lines.append('    "No dependencies";')
    else:
        for edge in internal_edges:
            lines.append(f'    "{edge.source}" -> "{edge.target}";')

    lines.append("}")
    return "\n".join(lines)
