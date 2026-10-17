"""Formatters package for RepoLens."""

from repolens.formatters.context import format_ai_context
from repolens.formatters.mermaid import to_dot, to_mermaid
from repolens.formatters.terminal import (
    format_file_explanation,
    format_full_report,
    format_hotspots_report,
    format_onboarding_report,
    format_terminal_scan,
)

__all__ = [
    "format_ai_context",
    "format_file_explanation",
    "format_full_report",
    "format_hotspots_report",
    "format_onboarding_report",
    "format_terminal_scan",
    "to_dot",
    "to_mermaid",
]
