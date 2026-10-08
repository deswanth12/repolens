# RepoLens Architecture

RepoLens is structured as a decoupled, multi-stage static analysis pipeline designed around deterministic repository evidence.

---

## High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Entry Point                          │
│        (repolens . | scan | onboard | hotspots | map)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   RepoLensEngine                            │
│     Orchestrates scanning, parsing, graph, intelligence     │
└──────────┬───────────────────┬───────────────────┬──────────┘
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────────┐ ┌───────────────┐ ┌───────────────────┐
│  Discovery Engine   │ │ AST Analyzers │ │ Dependency Graph  │
│  - Filesystem crawl │ │ - Python      │ │ - Module resolver │
│  - .gitignore spec  │ │ - JS / TS     │ │ - Degree metrics  │
│  - Language detect  │ │ - Fallback    │ │ - Cycle detection │
└─────────────────────┘ └───────────────┘ └───────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Intelligence Layer                       │
│  - EntryPointDetector (AST markers + pyproject / package.json)
│  - HotspotDetector (Graph coupling + symbol volume)         │
│  - ArchitectureInferer (Layers backed by evidence)          │
│  - ReadingOrderEngine (Optimal topological sequence)        │
│  - OnboardingPlanner (30-Minute contributor roadmap)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  - Terminal Formatter (Rich, ASCII-safe, clean hierarchy)   │
│  - JSON Serializer (Complete machine-readable payload)      │
│  - Graph Formatter (Mermaid flowchart, Graphviz DOT)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Data Models (`repolens/models.py`)
All internal data structures are defined as clean, strongly typed standard library `dataclasses`.
- `FileRecord`: Discovered file metadata, language, classification, size, line count.
- `ModuleAnalysis`: Symbols (functions, classes, methods), imports, exports, main block flags.
- `DependencyGraph`: In-memory directed graph of internal modules, external dependencies, and cycle lists.
- `EntryPointRecord`: Detected entry point, category, confidence, and cited reasons.
- `HotspotRecord`: Module with coupling metrics, symbol volume, and explainable role.
- `ArchitecturalLayer`: Inferred layer (CLI, API, Services, Storage, etc.) with supporting evidence points.
- `ReadingOrderItem`: Ordered item with concrete reading purpose.
- `OnboardingPlan`: Six-phase, 30-minute contributor roadmap.
- `FullAnalysisResult`: Aggregated data model with `.to_dict()` for clean JSON serialization.

### 2. Discovery Engine (`repolens/discovery/`)
- `scanner.py`: Traverses directories using `os.walk` with top-down directory pruning.
- `ignore.py`: Respects `.gitignore` rules via `pathspec` and automatically excludes `node_modules`, `.venv`, `.git`, `__pycache__`, `dist`, `build`, etc.
- `language.py`: Maps file extensions to languages and classifies files into `source`, `test`, `documentation`, `configuration`, or `other`.

### 3. AST Analyzers (`repolens/analyzers/`)
- `base.py`: Declares `BaseAnalyzer` interface.
- `python_analyzer.py`: Parses Python files using Python's standard library `ast` module.
- `js_ts_analyzer.py`: Parses JavaScript, TypeScript, and TSX files using prebuilt `tree-sitter` C grammars. Includes regex fallback.
- `fallback_analyzer.py`: Handles other languages safely, providing file-level structure with an explicit disclaimer.

### 4. Dependency Graph Engine (`repolens/graph/`)
- `resolver.py`: Pre-indexes repository modules and resolves relative (`from . import x`) and absolute (`from app.db import repo`) imports to internal repository paths. Classifies non-repo imports as external/stdlib dependencies.
- `builder.py`: Constructs internal directed edges, calculates in-degree (dependents) and out-degree (dependencies), and runs cycle detection.

### 5. Intelligence Engines (`repolens/intelligence/`)
- `entry_points.py`: Identifies application kickoffs using AST guards (`if __name__ == "__main__":`), CLI decorators (Click/Typer), and configuration manifests (`pyproject.toml` scripts, `package.json` bin/scripts).
- `hotspots.py`: Flags modules that act as foundational layers, central nexuses, or orchestrators without misleading 0-100 penalty scores.
- `architecture.py`: Identifies multi-tier layers backed by directory conventions and imported frameworks.
- `reading_order.py`: Produces a focused reading sequence (Docs $\to$ Config $\to$ Entry Point $\to$ Hotspots $\to$ Domain Models $\to$ Tests).
- `onboarding.py`: Converts findings into a time-boxed 30-minute contributor guide.

### 6. Formatters (`repolens/formatters/`)
- `terminal.py`: Terminal presentation using `Rich`, strictly configured with `legacy_windows=False` and ASCII divider characters for cross-platform resilience.
- `mermaid.py`: Mermaid diagram generation (`repolens map . --format mermaid`) and DOT export.
