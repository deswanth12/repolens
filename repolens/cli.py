"""CLI interface for RepoLens.

Built with Click and Rich for clean, responsive, and readable terminal output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from repolens import __version__
from repolens.discovery.scanner import RepositoryScanner
from repolens.models import RepositoryScanResult

console = Console(legacy_windows=False)
err_console = Console(stderr=True, legacy_windows=False)


def format_terminal_scan(result: RepositoryScanResult) -> None:
    """Renders a clean, professional summary of the repository scan to terminal."""
    s = result.summary

    # Header title
    title_text = Text()
    title_text.append("RepoLens ", style="bold cyan")
    title_text.append(f"v{__version__} -- Understand how a codebase works", style="dim")
    console.print(title_text)
    console.print("-" * 50, style="dim")

    # Project metadata table
    meta_table = Table(show_header=False, box=None, padding=(0, 2))
    meta_table.add_column("Key", style="bold white", width=18)
    meta_table.add_column("Value", style="cyan")

    meta_table.add_row("Project:", s.project_name)
    meta_table.add_row("Root Path:", s.root_path)
    meta_table.add_row("VCS:", "Git repository" if s.is_git else "Not a git repository")
    meta_table.add_row("Primary Language:", s.primary_language)
    console.print(meta_table)

    console.print("-" * 50, style="dim")

    # Metrics table
    metrics_table = Table(show_header=False, box=None, padding=(0, 2))
    metrics_table.add_column("Metric", style="bold white", width=18)
    metrics_table.add_column("Count", style="green")

    metrics_table.add_row("Total Files:", str(s.total_files))
    metrics_table.add_row("Source Files:", str(s.source_files))
    metrics_table.add_row("Test Files:", str(s.test_files))
    metrics_table.add_row("Documentation:", str(s.doc_files))
    metrics_table.add_row("Configuration:", str(s.config_files))
    metrics_table.add_row("Total Lines:", f"{s.total_lines:,}")
    metrics_table.add_row("Ignored Items:", str(s.ignored_count))
    console.print(metrics_table)

    # Language breakdown
    if s.languages:
        console.print("-" * 50, style="dim")
        console.print("[bold white]LANGUAGES[/bold white]")
        lang_table = Table(box=None, padding=(0, 2))
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", justify="right", style="white")
        lang_table.add_column("Lines", justify="right", style="white")
        lang_table.add_column("Share", justify="right", style="green")

        for l in s.languages[:8]:  # Show top 8 languages
            lang_table.add_row(
                l.language,
                str(l.file_count),
                f"{l.line_count:,}",
                f"{l.percentage}%",
            )
        console.print(lang_table)

    if s.warnings:
        console.print("-" * 50, style="dim")
        console.print("[bold yellow]WARNINGS[/bold yellow]")
        for w in s.warnings[:5]:
            console.print(f" [yellow]*[/yellow] {w}")

    console.print("-" * 50, style="dim")


class RepoLensGroup(click.Group):
    """Custom Click Group allowing flags like --json in any argument position."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        cleaned: list[str] = []
        for a in args:
            if a == "--json":
                ctx.params["json_output"] = True
            else:
                cleaned.append(a)
        return super().parse_args(ctx, cleaned)


@click.group(cls=RepoLensGroup, invoke_without_command=True)
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.version_option(version=__version__, prog_name="repolens")
@click.pass_context
def main(ctx: click.Context, path: str, json_output: bool) -> None:
    """RepoLens: Understand how a codebase works.

    Run 'repolens [PATH]' to analyze a repository.
    """
    if ctx.invoked_subcommand is None:
        run_scan(path=path, json_output=json_output or ctx.params.get("json_output", False))


@main.command(name="scan")
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def scan_cmd(ctx: click.Context, path: str, json_output: bool) -> None:
    """Discover repository structure, languages, and files."""
    run_scan(path=path, json_output=json_output or ctx.parent.params.get("json_output", False) if ctx.parent else json_output)


def run_scan(path: str, json_output: bool) -> None:
    target = Path(path).resolve()
    try:
        scanner = RepositoryScanner(target)
        result = scanner.scan()
    except Exception as e:
        err_console.print(f"[bold red]Error during scan:[/bold red] {e}")
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        format_terminal_scan(result)


if __name__ == "__main__":
    main()
