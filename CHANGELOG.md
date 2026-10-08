# Changelog

All notable changes to **RepoLens** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-08

### Added
- **Repository Discovery**:
  - Filesystem crawler with automatic `.gitignore` parsing (`pathspec`) and default ignore filters (`.venv`, `node_modules`, `__pycache__`, `dist`, `build`, etc.).
  - Language detection and file categorization (`source`, `test`, `documentation`, `configuration`, `build`, `other`).
- **AST Multi-Language Analyzers**:
  - `PythonAnalyzer`: Built-in safe standard library `ast` parsing for functions, classes, methods, decorators, imports, exports (`__all__`), and entry-point guards (`if __name__ == "__main__":`).
  - `JavaScriptTypeScriptAnalyzer`: C-level AST parsing via `tree-sitter` for JavaScript, TypeScript, and TSX files, extracting imports, exports, functions, classes, and server lifecycle markers.
  - `FallbackAnalyzer`: Graceful fallback reporting for unsupported languages (Go, Rust, Java, C/C++, C#, etc.) with transparent limitation disclaimers.
- **Dependency Graph Engine**:
  - Internal directed module dependency graph with path resolution for relative and package imports.
  - Calculation of in-degree (dependents), out-degree (dependencies), and graph cycle detection.
- **Evidence-Based Intelligence**:
  - `EntryPointDetector`: Evidence-backed entry point detection combining AST patterns, CLI decorators, and packaging manifests (`pyproject.toml`, `package.json`).
  - `HotspotDetector`: High-connectivity hub detection with human-readable structural interpretations (foundational modules, orchestrators, structural nexuses) without arbitrary 0-100 scores.
  - `ArchitectureInferer`: Automated architectural layer classification (CLI, API, Services, Data Access, Utilities, Configuration, Tests) backed by concrete source evidence.
  - `ReadingOrderEngine`: Prioritized sequence of high-leverage files to read first.
  - `OnboardingPlanner`: "Your First 30 Minutes" phased walkthrough for new contributors.
- **CLI Commands**:
  - `repolens .`: Full codebase understanding report.
  - `repolens scan .`: Fast filesystem discovery.
  - `repolens onboard .`: 30-minute contributor onboarding blueprint.
  - `repolens hotspots .`: Detailed structural code hotspots.
  - `repolens map . [--format mermaid|dot|json]`: Dependency graph visualization.
  - `repolens explain <path>`: Single file architectural breakdown.
  - `repolens report . [--format json|text]`: Machine-readable structured JSON export.
- **Security Guarantees**:
  - 100% static analysis, zero code execution, zero network requests, local-first privacy.
