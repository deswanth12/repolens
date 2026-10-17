"""AI Context Pack formatter for RepoLens.

Produces dense, evidence-based Markdown designed specifically to give
AI coding assistants (Claude Code, Cursor, Copilot, ChatGPT, Antigravity)
a grounded architectural map of a codebase before editing.
"""

from __future__ import annotations

from repolens.formatters.mermaid import to_mermaid
from repolens.models import FullAnalysisResult, SymbolType


def format_ai_context(
    result: FullAnalysisResult,
    include_mermaid: bool = True,
    max_hotspots: int = 7,
) -> str:
    """Format full analysis result into a structured Markdown AI context pack.

    Distinguishes verified AST facts from heuristic recommendations and
    transparently notes analysis scope and limitations.
    """
    summary = result.scan.summary
    lines: list[str] = []

    # Title & Header
    lines.append(f"# Codebase Intelligence: {summary.project_name}")
    lines.append("")
    lines.append("> RepoLens — Give your AI coding assistant a grounded map of your codebase before it starts editing.")
    lines.append(
        "> Local-first static analysis. Verified facts are extracted directly from code structure; "
        "architectural tiers and reading sequences are heuristic recommendations."
    )
    lines.append("")

    # 1. Project Profile & Scale (Verified Facts)
    lines.append("## 1. Project Profile & Scale (Verified Facts)")
    lines.append(f"- **Project Name**: `{summary.project_name}`")
    lines.append(f"- **Primary Language**: {summary.primary_language}")
    lines.append(
        f"- **Codebase Scale**: {summary.source_files} source files | "
        f"{summary.test_files} test files | {summary.total_files} total files | "
        f"{summary.total_lines:,} lines of code"
    )
    if summary.languages:
        lang_parts = [
            f"{lang.language} ({lang.percentage:.1f}%, {lang.file_count} files)"
            for lang in summary.languages
        ]
        lines.append(f"- **Languages Detected**: {', '.join(lang_parts)}")
    lines.append("")

    # 2. Application Entry Points (Verified Facts)
    lines.append("## 2. Application Entry Points (Verified Facts)")
    if result.entry_points:
        lines.append("Execution enters the codebase through these detected starting points:")
        lines.append("")
        lines.append("| Entry Point | Category | Confidence | Rationale / Evidence |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for ep in result.entry_points:
            reasons = "; ".join(ep.reasons) if ep.reasons else "Direct entry point candidate"
            lines.append(f"| `{ep.rel_path}` | {ep.category} | {ep.confidence.value} | {reasons} |")
        lines.append("")
        lines.append("*Guidance*: Trace execution flow beginning from these files.")
    else:
        lines.append("No explicit top-level application entry points detected (library/utility collection).")
    lines.append("")

    # 3. Architectural Layers (Heuristic Recommendation)
    lines.append("## 3. Inferred Architecture & Layers (Heuristic)")
    if result.layers:
        lines.append("The repository is heuristically organized into the following architectural tiers:")
        lines.append("")
        lines.append("| Tier / Layer | Confidence | Key Files |")
        lines.append("| :--- | :--- | :--- |")
        for layer in result.layers:
            sample_files = ", ".join(f"`{f}`" for f in layer.files[:4])
            if len(layer.files) > 4:
                sample_files += f" *(+{len(layer.files) - 4} more)*"
            lines.append(f"| **{layer.layer_name}** | {layer.confidence.value} | {sample_files} |")
        lines.append("")
    else:
        lines.append("Flat or monolithic architecture; no distinct layered subdirectories inferred.")
    lines.append("")

    # 4. Critical Hotspots & Core Interfaces (Verified AST Coupling)
    lines.append("## 4. Architectural Hotspots (High-Connectivity Hubs)")
    if result.hotspots:
        lines.append(
            "These modules have the highest connectivity across the system. Changes here have high blast radius:"
        )
        lines.append("")
        selected_hotspots = result.hotspots[:max_hotspots]
        for h in selected_hotspots:
            lines.append(f"### `{h.rel_path}`")
            lines.append(
                f"- **Connectivity**: {h.dependent_count} dependents | {h.dependency_count} dependencies | {h.symbol_count} symbols"
            )
            if h.interpretation:
                lines.append(f"- **Role**: {h.interpretation}")

            analysis = result.analyses.get(h.rel_path)
            if analysis and analysis.symbols:
                core_symbols = [
                    s
                    for s in analysis.symbols
                    if s.symbol_type in (SymbolType.CLASS, SymbolType.FUNCTION, SymbolType.ASYNC_FUNCTION)
                    and not s.name.startswith("_")
                ]
                if core_symbols:
                    lines.append("- **Exported Symbols**:")
                    for s in core_symbols[:8]:
                        doc = f" - {s.docstring.splitlines()[0]}" if s.docstring else ""
                        lines.append(f"  - `{s.symbol_type.value} {s.name}`{doc}")
            lines.append("")
    else:
        lines.append("No high-connectivity hotspot modules detected.")
    lines.append("")

    # 5. Recommended Reading Sequence (Heuristic Guidance)
    lines.append("## 5. Recommended Reading Sequence (Heuristic)")
    if result.reading_order:
        lines.append("To understand how this repository works in the fewest steps, inspect files in this progressive order:")
        lines.append("")
        for item in result.reading_order[:8]:
            lines.append(f"{item.order}. `{item.rel_path}` ({item.category}) - {item.purpose}")
        lines.append("")

    # 6. Architecture & Dependency Map (Mermaid)
    if include_mermaid:
        lines.append("## 6. Dependency Map")
        lines.append("```mermaid")
        lines.append(to_mermaid(result.graph, max_edges=40))
        lines.append("```")
        lines.append("")

    # 7. AI Agent Guardrails & Invariants
    lines.append("## 7. AI Agent Guardrails & Invariants")
    cycle_count = len(result.graph.cycles)
    cycle_note = (
        f"[Warning] There are currently {cycle_count} circular dependency chains. Avoid introducing more."
        if cycle_count > 0
        else "[OK] Zero circular dependencies detected. Keep module imports acyclic."
    )
    lines.append(f"1. **Cycle Invariant**: {cycle_note}")
    if result.hotspots:
        top_h = ", ".join(f"`{h.rel_path}`" for h in result.hotspots[:3])
        lines.append(
            f"2. **Blast Radius Invariant**: Modifying {top_h} impacts multiple consumers. Always run affected tests after editing core hubs."
        )
    lines.append(
        "3. **Layer Separation**: Higher layers (e.g. CLI) orchestrate lower layers (Domain/Engine/Storage). Avoid reverse dependencies from domain logic into CLI."
    )
    lines.append(
        "4. **Verification**: Always run existing test suites to confirm runtime behavior before committing changes."
    )
    lines.append("")

    # 8. Analysis Scope & Limitations
    lines.append("## 8. Analysis Scope & Limitations")
    modes = {a.analysis_mode for a in result.analyses.values() if a.analysis_mode}
    mode_desc: list[str] = []
    if "ast" in modes:
        mode_desc.append("Native AST (Python)")
    if "tree_sitter" in modes:
        mode_desc.append("Tree-Sitter AST (JS/TS)")
    if "regex_fallback" in modes:
        mode_desc.append("Regex Fallback (Structural heuristics only)")
    lines.append(f"- **Analysis Modes Active**: {', '.join(mode_desc) if mode_desc else 'Static inspection'}")

    if summary.warnings:
        lines.append(f"- **Scan Warnings ({len(summary.warnings)})**:")
        for w in summary.warnings[:5]:
            lines.append(f"  - {w}")
    else:
        lines.append("- **Scan Warnings**: None (all files cleanly parsed within size and security limits).")

    lines.append(
        "- **Grounding Note**: Static analysis provides structural evidence to guide AI reasoning, "
        "but does not guarantee runtime semantics or replace test execution."
    )
    lines.append("")

    return "\n".join(lines).strip() + "\n"
