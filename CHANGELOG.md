# Changelog

All notable changes to **RepoLens** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **AI Agent Context Pack (`repolens context`)**: Added `repolens context [PATH] [-o AGENTS.md]` command to generate dense, token-efficient Markdown context packs (~1,500 tokens) designed specifically to ground AI coding assistants (Claude Code, Cursor, Copilot, ChatGPT, Antigravity) with an accurate architectural mental model without prompt bloat.
- **Markdown Export Format (`--format markdown`)**: Added `--format markdown` option across `repolens [PATH]` and `repolens report [PATH]`, outputting clean GitHub Flavored Markdown with embedded Mermaid dependency diagrams.

## [0.1.2] - 2026-10-15

### Fixed
- **Cross-Language Comment Keyword Leakage**: Scoped regex import detection in `FallbackAnalyzer` to language-specific patterns and anchored to line starts. Fixed bug where comments like `// use click events` in Go files falsely registered Python `click` imports and misclassified projects into Python CLI architecture.
- **Accurate Fallback Reporting**: Removed misleading `parse_error` on valid unsupported-language files (Go, Rust, Ruby, etc.) in `FallbackAnalyzer`. Graceful fallback is now cleanly reported via `analysis_mode="regex_fallback"` and informative `warnings` without falsely marking valid files as broken.
- **Compiled Language Entry Points**: Added standard entry-point heuristics for Go (`main.go`), Rust (`main.rs`), C (`main.c`), C++ (`main.cpp`, `main.cc`), and Java (`Main.java`).
- **Canonical README Prioritization**: Fixed alphabetical priority distortion in `ReadingOrderEngine` and `OnboardingPlanner` that caused auxiliary root documentation (e.g. `README-VIM.md`, `README.zh-CN.md`) to be selected as step 1 instead of canonical `README.md`.
- **Package Execution Support**: Added `repolens/__main__.py` to support running `python -m repolens` in environments where script entrypoints are not added to PATH.
- **CLI Root Format Option**: Added `--format [text|json]` option to root `repolens [PATH]` invocation, eliminating option mismatch errors when users run `repolens . --format json`.
- **JSON Module Export**: Included full AST module analyses (`modules`) in `FullAnalysisResult.to_dict()` for downstream consumers and AI agents.

### Added
- **Dual Console Script Alias**: Registered both `repolens` and `repolens-toolkit` console script entrypoints in `pyproject.toml` for seamless `pipx run repolens-toolkit` and `repolens` usage.

## [0.1.1] - 2026-10-09

### Fixed
- **Python 3.10 Compatibility**: Resolved `tomllib` unavailability in Python 3.10 environments by declaring `tomli>=1.1.0;python_version<'3.11'` in dependencies and providing regex fallback parsing for `[project.scripts]`.
- **CI / Release Workflow Validation**: Repaired duplicate YAML keys in `.github/workflows/release.yml` and verified matrix testing across Python 3.10, 3.11, and 3.12 on Linux, Windows, and macOS.
- **Contributing Guide**: Fixed repository clone URL in `CONTRIBUTING.md` to point to active repository `deswanth12/repolens`.

### Added
- **PyPA Trusted Publishing**: Added dedicated GitHub Actions publishing workflow (`.github/workflows/publish-pypi.yml`) configured for OIDC token-based publication to PyPI with manual environment gating.
- **Troubleshooting & FAQ Documentation**: Added comprehensive troubleshooting section in `README.md` covering monorepo subprojects, custom ignore flags (`-i`), 2 MB file limits, and unsupported language fallbacks.
- **Frictionless Installation Options**: Documented direct wheel and git installation one-liners in `README.md`.
- **PyPI Distribution**: Configured official PyPI distribution name as `repolens-toolkit` (installable via `pip install repolens-toolkit`).
- **Launch & Feedback Kit**: Created `docs/LAUNCH_KIT.md` containing verified demonstration scripts, launch messaging, outreach templates, and structured feedback logging.

### Changed
- Explicitly excluded `.mypy_cache/` and `.ruff_cache/` in `.gitignore`.

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
