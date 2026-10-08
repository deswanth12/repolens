"""CLI interface for RepoLens.

Built with Click and Rich for clean, responsive, and readable terminal output.
Provides full repository understanding, onboarding plans, dependency maps, and hotspot detection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console

from repolens import __version__
from repolens.discovery.scanner import RepositoryScanner
from repolens.engine import RepoLensEngine
from repolens.formatters import (
    format_file_explanation,
    format_full_report,
    format_hotspots_report,
    format_onboarding_report,
    to_dot,
    to_mermaid,
)

console = Console(legacy_windows=False)
err_console = Console(stderr=True, legacy_windows=False)


class RepoLensGroup(click.Group):
    """Custom Click Group allowing flags like --json and root arguments seamlessly."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        cleaned: list[str] = []
        for a in args:
            if a == "--json":
                ctx.params["json_output"] = True
            else:
                cleaned.append(a)

        if cleaned and cleaned[0] not in self.commands and not cleaned[0].startswith("-"):
            ctx.params["path"] = cleaned.pop(0)
        else:
            ctx.params["path"] = "."

        return super().parse_args(ctx, cleaned)


@click.group(cls=RepoLensGroup, invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.version_option(version=__version__, prog_name="repolens")
@click.pass_context
def main(ctx: click.Context, json_output: bool, path: str = ".") -> None:
    """RepoLens: Understand how a codebase works.

    Run 'repolens [PATH]' to analyze a repository and generate an explainable map.
    """
    if ctx.invoked_subcommand is None:
        run_full_analysis(path=path, json_output=json_output or ctx.params.get("json_output", False))


@main.command(name="scan")
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def scan_cmd(ctx: click.Context, path: str, json_output: bool) -> None:
    """Discover repository structure, languages, and files."""
    run_quick_scan(path=path, json_output=json_output or (ctx.parent.params.get("json_output", False) if ctx.parent else False))


@main.command(name="onboard")
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def onboard_cmd(ctx: click.Context, path: str, json_output: bool) -> None:
    """Generate 'Your First 30 Minutes' contributor onboarding blueprint."""
    target = Path(path).resolve()
    engine = RepoLensEngine(target)
    result = engine.analyze()

    is_json = json_output or (ctx.parent.params.get("json_output", False) if ctx.parent else False)
    if is_json:
        click.echo(json.dumps(result.onboarding.to_dict(), indent=2))
    else:
        format_onboarding_report(result.onboarding)


@main.command(name="hotspots")
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def hotspots_cmd(ctx: click.Context, path: str, json_output: bool) -> None:
    """Identify structural dependency hotspots and central coordination modules."""
    target = Path(path).resolve()
    engine = RepoLensEngine(target)
    result = engine.analyze()

    is_json = json_output or (ctx.parent.params.get("json_output", False) if ctx.parent else False)
    if is_json:
        click.echo(json.dumps([h.to_dict() for h in result.hotspots], indent=2))
    else:
        format_hotspots_report(result.hotspots)


@main.command(name="map")
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["mermaid", "dot", "json"], case_sensitive=False),
    default="mermaid",
    help="Diagram format (mermaid, dot, json).",
)
def map_cmd(path: str, fmt: str) -> None:
    """Generate visual module dependency graph."""
    target = Path(path).resolve()
    engine = RepoLensEngine(target)
    result = engine.analyze()

    if fmt == "dot":
        click.echo(to_dot(result.graph))
    elif fmt == "json":
        click.echo(json.dumps(result.graph.to_dict(), indent=2))
    else:
        click.echo(to_mermaid(result.graph))


@main.command(name="explain")
@click.argument("file_path", type=str)
@click.option("--repo", default=".", type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Repository root.")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
def explain_cmd(file_path: str, repo: str, json_output: bool) -> None:
    """Explain a specific file: symbols, dependencies, and architectural role."""
    target_repo = Path(repo).resolve()
    engine = RepoLensEngine(target_repo)
    result = engine.analyze()

    # Normalize file_path to POSIX relative path
    norm_path = file_path.replace("\\", "/").lstrip("./")

    if json_output:
        analysis = result.analyses.get(norm_path)
        node = result.graph.nodes.get(norm_path)
        payload = {
            "file": norm_path,
            "analysis": analysis.to_dict() if analysis else None,
            "graph_node": node.to_dict() if node else None,
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        format_file_explanation(norm_path, result)


@main.command(name="report")
@click.argument("path", default=".", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Report format (text, json).",
)
def report_cmd(path: str, fmt: str) -> None:
    """Output complete codebase understanding report."""
    run_full_analysis(path=path, json_output=(fmt == "json"))


def run_full_analysis(path: str, json_output: bool) -> None:
    target = Path(path).resolve()
    try:
        engine = RepoLensEngine(target)
        result = engine.analyze()
    except Exception as e:
        err_console.print(f"[bold red]Error during analysis:[/bold red] {e}")
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        format_full_report(result)


def run_quick_scan(path: str, json_output: bool) -> None:
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
        from repolens.formatters import format_terminal_scan
        format_terminal_scan(result)


if __name__ == "__main__":
    main()
