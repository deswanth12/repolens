"""Central execution engine for RepoLens.

Orchestrates repository scanning, multi-language AST analysis,
graph construction, intelligence deduction, and reporting.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from repolens.analyzers.base import BaseAnalyzer
from repolens.analyzers.fallback_analyzer import FallbackAnalyzer
from repolens.analyzers.js_ts_analyzer import JavaScriptTypeScriptAnalyzer
from repolens.analyzers.python_analyzer import PythonAnalyzer
from repolens.discovery.scanner import RepositoryScanner
from repolens.graph.builder import DependencyGraphBuilder
from repolens.intelligence.architecture import ArchitectureInferer
from repolens.intelligence.entry_points import EntryPointDetector
from repolens.intelligence.hotspots import HotspotDetector
from repolens.intelligence.onboarding import OnboardingPlanner
from repolens.intelligence.reading_order import ReadingOrderEngine
from repolens.models import (
    FileCategory,
    FullAnalysisResult,
    ModuleAnalysis,
)


class RepoLensEngine:
    """End-to-end repository understanding engine."""

    def __init__(
        self,
        root_path: str | Path,
        custom_ignores: Iterable[str] | None = None,
        respect_gitignore: bool = True,
    ) -> None:
        self.root_path = Path(root_path).resolve()
        self.custom_ignores = list(custom_ignores or [])
        self.respect_gitignore = respect_gitignore

        # Registered language analyzers in priority order
        self.analyzers: list[BaseAnalyzer] = [
            PythonAnalyzer(),
            JavaScriptTypeScriptAnalyzer(),
            FallbackAnalyzer(),
        ]

    def analyze(self) -> FullAnalysisResult:
        """Executes full repository intelligence pipeline."""
        # 1. Discover filesystem structure and files
        scanner = RepositoryScanner(
            self.root_path,
            custom_ignores=self.custom_ignores,
            respect_gitignore=self.respect_gitignore,
        )
        scan_result = scanner.scan()

        # 2. Parse source files through language analyzers
        analyses: dict[str, ModuleAnalysis] = {}
        for f in scan_result.files:
            if f.category in {FileCategory.SOURCE, FileCategory.TEST} and not f.is_binary:
                file_full_path = self.root_path / f.rel_path
                for analyzer in self.analyzers:
                    if analyzer.can_analyze(f):
                        analysis = analyzer.analyze(file_full_path, f.rel_path)
                        analyses[f.rel_path] = analysis
                        break

        # 3. Construct module dependency graph
        graph_builder = DependencyGraphBuilder(analyses)
        graph = graph_builder.build()

        # 4. Intelligence deductions
        ep_detector = EntryPointDetector(self.root_path, analyses)
        entry_points = ep_detector.detect()

        hotspot_detector = HotspotDetector(graph, analyses)
        hotspots = hotspot_detector.detect()

        arch_inferer = ArchitectureInferer(scan_result.files, analyses, graph)
        layers = arch_inferer.infer()

        ro_engine = ReadingOrderEngine(scan_result.files, entry_points, hotspots)
        reading_order = ro_engine.generate()

        onboarding_planner = OnboardingPlanner(
            project_name=scan_result.summary.project_name,
            files=scan_result.files,
            entry_points=entry_points,
            hotspots=hotspots,
            layers=layers,
            reading_order=reading_order,
        )
        onboarding = onboarding_planner.plan()

        return FullAnalysisResult(
            scan=scan_result,
            analyses=analyses,
            graph=graph,
            entry_points=entry_points,
            hotspots=hotspots,
            layers=layers,
            reading_order=reading_order,
            onboarding=onboarding,
        )
