"""Terminal formatters for RepoLens using Rich.

Produces clean, readable, professional terminal reports without tacky formatting.
Safe for all terminal encodings (ASCII-resilient).
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.text import Text

from repolens import __version__
from repolens.models import (
    FullAnalysisResult,
    HotspotRecord,
    OnboardingPlan,
    RepositoryScanResult,
)

console = Console(legacy_windows=False)
err_console = Console(stderr=True, legacy_windows=False)


def print_divider() -> None:
    console.print("-" * 60, style="dim")


def format_full_report(result: FullAnalysisResult) -> None:
    """Renders the comprehensive codebase understanding report."""
    s = result.scan.summary

    # Header
    title = Text()
    title.append("RepoLens ", style="bold cyan")
    title.append(f"v{__version__} -- Understand how a codebase works", style="dim")
    console.print(title)
    print_divider()

    # Repository Overview Table
    meta_table = Table(show_header=False, box=None, padding=(0, 2))
    meta_table.add_column("Key", style="bold white", width=20)
    meta_table.add_column("Value", style="cyan")

    meta_table.add_row("Project:", s.project_name)
    meta_table.add_row("Root Path:", s.root_path)
    meta_table.add_row("Primary Language:", s.primary_language)
    meta_table.add_row("Files (Total / Source):", f"{s.total_files} total / {s.source_files} source")
    meta_table.add_row("Tests / Docs:", f"{s.test_files} tests / {s.doc_files} docs")
    meta_table.add_row("Total Lines:", f"{s.total_lines:,}")
    meta_table.add_row("Entry Points:", str(len(result.entry_points)))
    console.print(meta_table)

    # Inferred Architecture
    if result.layers:
        print_divider()
        console.print("[bold white]INFERRED ARCHITECTURE[/bold white]")
        arch_table = Table(box=None, padding=(0, 2))
        arch_table.add_column("Layer", style="bold cyan")
        arch_table.add_column("Confidence", style="green")
        arch_table.add_column("Files & Evidence", style="white")

        for layer in result.layers:
            files_str = ", ".join(layer.files[:3])
            if len(layer.files) > 3:
                files_str += f" (+{len(layer.files) - 3} more)"
            evidence_summary = layer.evidence[0] if layer.evidence else ""
            desc = f"[cyan]{files_str}[/cyan]\n[dim]{evidence_summary}[/dim]" if evidence_summary else files_str
            arch_table.add_row(layer.layer_name, layer.confidence.value.upper(), desc)
        console.print(arch_table)

    # Entry Points
    if result.entry_points:
        print_divider()
        console.print("[bold white]APPLICATION ENTRY POINTS[/bold white]")
        ep_table = Table(box=None, padding=(0, 2))
        ep_table.add_column("File", style="cyan")
        ep_table.add_column("Category", style="yellow")
        ep_table.add_column("Confidence", style="green")
        ep_table.add_column("Evidence", style="white")

        for ep in result.entry_points[:4]:
            reason_str = ep.reasons[0] if ep.reasons else "Entry point convention"
            ep_table.add_row(ep.rel_path, ep.category, ep.confidence.value.upper(), reason_str)
        console.print(ep_table)

    # Dependency Hotspots
    if result.hotspots:
        print_divider()
        console.print("[bold white]STRUCTURAL HOTSPOTS[/bold white] [dim](High connectivity / Core coordination)[/dim]")
        hs_table = Table(box=None, padding=(0, 2))
        hs_table.add_column("Module", style="cyan")
        hs_table.add_column("Coupling (In/Out)", style="yellow")
        hs_table.add_column("Role / Interpretation", style="white")

        for hs in result.hotspots[:5]:
            coupling = f"{hs.dependent_count} callers / {hs.dependency_count} imports"
            hs_table.add_row(hs.rel_path, coupling, hs.interpretation)
        console.print(hs_table)

    # Recommended Reading Order
    if result.reading_order:
        print_divider()
        console.print("[bold white]RECOMMENDED READING ORDER[/bold white]")
        ro_table = Table(box=None, padding=(0, 2))
        ro_table.add_column("#", style="bold green", width=4)
        ro_table.add_column("File", style="cyan")
        ro_table.add_column("Category", style="yellow")
        ro_table.add_column("Why Read This", style="white")

        for ro in result.reading_order:
            ro_table.add_row(str(ro.order), ro.rel_path, ro.category, ro.purpose)
        console.print(ro_table)

    # Next file to read banner
    if result.reading_order:
        next_step = result.reading_order[0]
        print_divider()
        console.print(f"[bold green]NEXT FILE TO READ:[/bold green] [bold cyan]{next_step.rel_path}[/bold cyan]")
        console.print(f"[dim]{next_step.purpose}[/dim]")

    print_divider()


def format_onboarding_report(plan: OnboardingPlan) -> None:
    """Renders the 30-minute contributor onboarding blueprint."""
    title = Text()
    title.append("RepoLens ", style="bold cyan")
    title.append(f"v{__version__} -- Contributor Onboarding: {plan.project_name}", style="dim")
    console.print(title)
    print_divider()
    console.print("[bold white]YOUR FIRST 30 MINUTES[/bold white]")
    console.print("[dim]A structured, time-boxed roadmap to build a working mental model.[/dim]\n")

    for p in plan.phases:
        console.print(f"[bold green][{p.time_window}][/bold green] [bold white]{p.focus}[/bold white]")
        targets_str = ", ".join(p.target_files)
        console.print(f"  [bold cyan]Files to open:[/bold cyan] {targets_str}")
        console.print(f"  [bold yellow]What to understand:[/bold yellow] {p.takeaway}\n")

    print_divider()


def format_hotspots_report(hotspots: list[HotspotRecord]) -> None:
    """Renders detailed structural hotspot analysis."""
    title = Text()
    title.append("RepoLens ", style="bold cyan")
    title.append(f"v{__version__} -- Structural Code Hotspots", style="dim")
    console.print(title)
    print_divider()

    if not hotspots:
        console.print("[yellow]No high-connectivity modules detected.[/yellow]")
        return

    table = Table(box=None, padding=(0, 2))
    table.add_column("Module", style="bold cyan", width=30)
    table.add_column("Dependents", justify="right", style="green", width=12)
    table.add_column("Dependencies", justify="right", style="yellow", width=14)
    table.add_column("Symbols", justify="right", style="white", width=10)
    table.add_column("Interpretation", style="white")

    for hs in hotspots:
        table.add_row(
            hs.rel_path,
            str(hs.dependent_count),
            str(hs.dependency_count),
            str(hs.symbol_count),
            hs.interpretation,
        )
    console.print(table)
    print_divider()


def format_file_explanation(rel_path: str, result: FullAnalysisResult) -> None:
    """Renders a detailed explanation of a single file."""
    analysis = result.analyses.get(rel_path)
    node = result.graph.nodes.get(rel_path)

    title = Text()
    title.append("RepoLens Explain: ", style="bold cyan")
    title.append(rel_path, style="bold white")
    console.print(title)
    print_divider()

    if not analysis:
        # Check if it exists in scanned files
        scanned = next((f for f in result.scan.files if f.rel_path == rel_path), None)
        if scanned:
            console.print(f"[yellow]File exists ({scanned.language}, {scanned.category.value}), but has no AST analysis.[/yellow]")
        else:
            console.print(f"[red]File '{rel_path}' not found in repository.[/red]")
        print_divider()
        return

    meta_table = Table(show_header=False, box=None, padding=(0, 2))
    meta_table.add_column("Key", style="bold white", width=18)
    meta_table.add_column("Value", style="cyan")

    meta_table.add_row("Language:", analysis.language)
    meta_table.add_row("Symbols Defined:", str(len(analysis.symbols)))
    meta_table.add_row("Total Imports:", str(len(analysis.imports)))
    if node:
        meta_table.add_row("Internal Callers:", f"{node.dependent_count} modules")
        meta_table.add_row("Internal Dependencies:", f"{node.dependency_count} modules")
    meta_table.add_row("Has Entry Guard:", "Yes" if analysis.has_main_block else "No")
    console.print(meta_table)

    # Defined symbols
    if analysis.symbols:
        print_divider()
        console.print("[bold white]DEFINED SYMBOLS[/bold white]")
        for s in analysis.symbols[:15]:
            kind = s.symbol_type.value.capitalize()
            parent = f"in {s.parent_symbol}." if s.parent_symbol else ""
            doc = f" -- {s.docstring}" if s.docstring else ""
            console.print(f"  [cyan]{kind}[/cyan] [bold white]{parent}{s.name}[/bold white]{doc}")

    # Dependent modules
    if node and node.dependents:
        print_divider()
        console.print("[bold white]IMPORTED BY (DEPENDENTS)[/bold white]")
        for dep in node.dependents:
            console.print(f"  [green]<-[/green] {dep}")

    # Outgoing dependencies
    if node and node.dependencies:
        print_divider()
        console.print("[bold white]DEPENDS ON (INTERNAL)[/bold white]")
        for dep in node.dependencies:
            console.print(f"  [yellow]->[/yellow] {dep}")

    print_divider()


def format_terminal_scan(scan_result: RepositoryScanResult) -> None:
    """Renders quick repository discovery scan in the terminal."""
    s = scan_result.summary
    title = Text()
    title.append("RepoLens ", style="bold cyan")
    title.append(f"v{__version__} -- Repository Scan: {s.project_name}", style="dim")
    console.print(title)
    print_divider()

    meta_table = Table(show_header=False, box=None, padding=(0, 2))
    meta_table.add_column("Key", style="bold white", width=24)
    meta_table.add_column("Value", style="cyan")

    meta_table.add_row("Project:", s.project_name)
    meta_table.add_row("Root Path:", s.root_path)
    meta_table.add_row("Primary Language:", s.primary_language)
    meta_table.add_row("Files (Total / Source):", f"{s.total_files} total / {s.source_files} source")
    meta_table.add_row("Tests / Docs:", f"{s.test_files} tests / {s.doc_files} docs")
    meta_table.add_row("Configuration Files:", str(s.config_files))
    meta_table.add_row("Total Lines:", f"{s.total_lines:,}")
    meta_table.add_row("Ignored Items:", str(s.ignored_count))
    console.print(meta_table)

    if s.languages:
        print_divider()
        console.print("[bold white]DETECTED LANGUAGES[/bold white]")
        lang_table = Table(box=None, padding=(0, 2))
        lang_table.add_column("Language", style="bold cyan")
        lang_table.add_column("Files", justify="right", style="green")
        lang_table.add_column("Lines", justify="right", style="yellow")
        lang_table.add_column("Share", justify="right", style="white")

        for lang in s.languages:
            lang_table.add_row(lang.language, str(lang.file_count), f"{lang.line_count:,}", f"{lang.percentage:.1f}%")
        console.print(lang_table)

    if s.warnings:
        print_divider()
        console.print(f"[bold yellow]Warnings ({len(s.warnings)}):[/bold yellow]")
        for w in s.warnings[:5]:
            console.print(f"  [dim]- {w}[/dim]")

    print_divider()

