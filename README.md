# RepoLens

<p align="center">
  <strong>Understand how a codebase works.</strong>
</p>

<p align="center">
  A local-first, evidence-based code intelligence and developer onboarding tool.<br>
  No arbitrary 0–100 scores. No repository code execution. No LLM keys required.
</p>

<p align="center">
  <a href="https://github.com/deswanth12/repolens/actions/workflows/ci.yml"><img src="https://github.com/deswanth12/repolens/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/deswanth12/repolens/releases"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Release Version"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Code style: ruff"></a>
  <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/types-mypy-blue.svg" alt="Types: Mypy"></a>
  <img src="https://img.shields.io/badge/telemetry-zero-success.svg" alt="Zero Telemetry">
</p>

---

## The Core Problem

> *"I cloned this repository. How does it actually work?"*

When developers, students, open-source contributors, and engineering teams approach an unfamiliar codebase, they are forced to open dozens of files manually, guess where execution begins, and piece together the mental model from scratch.

Existing tools either:
- **Lint your code** and tell you what you did wrong (`ruff`, `eslint`, `sonarqube`).
- **Draw unreadable spiderwebs** of 300 raw dependency edges (`madge`, `pydeps`).
- **Enforce architectural contracts** that require you to already understand the architecture before writing the rules (`import-linter`, `archunit`).
- **Dump raw files into LLM prompts** (`repomix`, chat assistants) which cost money, hallucinate, and send proprietary code to external clouds.

**RepoLens answers the core onboarding questions using deterministic repository evidence:**
- Where does this application start?
- What are the important modules?
- Which files depend on which other files?
- What are the main architectural layers?
- Which modules are central coordination hotspots?
- Which files should I read first, in what order, and why?
- What should a new contributor understand in their first 30 minutes?

---

## Key Features

- 🔍 **Evidence-Based Entry Points**: Identifies execution starting points using AST guards (`if __name__ == "__main__":`), CLI decorators (Click, Typer), and configuration manifests (`pyproject.toml` scripts, `package.json` bins).
- 🧭 **Recommended Reading Order**: Generates a sequential reading roadmap with an explicit purpose for each file (Documentation $\to$ Manifest $\to$ Entry Point $\to$ Hotspots $\to$ Domain Models $\to$ Tests).
- ⏱️ **The First 30 Minutes (`repolens onboard`)**: A time-boxed contributor onboarding blueprint broken down into 6 focused phases with specific files and conceptual takeaways.
- ⚡ **Structural Hotspots (Without Defect Scoring)**: High-connectivity modules identified and classified (Foundational Modules, Orchestrators, Structural Nexuses). Connectivity is treated as structural significance, not a "bad code" penalty.
- 🏛️ **Architectural Layer Inference**: Automatically detects multi-tier layers (`CLI`, `API`, `Services`, `Data Access / Storage`, `Utilities`, `Configuration`, `Tests`) backed by observable evidence.
- 🗺️ **Dependency Maps**: Generates clean, copy-pasteable Mermaid flowcharts and Graphviz DOT diagrams with `repolens map`.
- 🤖 **Machine-Readable JSON**: Full structured payload export via `repolens report . --format json`.
- 🔒 **Zero-Execution Security**: Never runs `eval()`, `exec()`, user imports, shell scripts, or test runners. 100% static AST parsing.
- 🌐 **100% Offline & Private**: Zero network calls, zero telemetry, zero tracking, zero external APIs.

---

## Quickstart

### Installation

```bash
# Clone and install locally
git clone https://github.com/deswanth12/repolens.git
cd repolens
pip install -e .
```

### Basic Usage

Run RepoLens on any directory:

```bash
# Analyze current repository
repolens .

# Or analyze a specific repository path
repolens path/to/project
```

---

## Example Output

```text
RepoLens v0.1.0 -- Understand how a codebase works
------------------------------------------------------------
  Project:              DevIntel
  Root Path:            C:\DevIntel
  Primary Language:     Python
  Files (Total/Source): 28 total / 18 source
  Tests / Docs:         11 tests / 5 docs
  Total Lines:          4,120
  Entry Points:         1
------------------------------------------------------------
INFERRED ARCHITECTURE
  Layer                 Confidence    Files & Evidence
  CLI / Interface       HIGH          repolens/cli.py
                                      Configured as console script 'repolens'
  Data Access / Storage MEDIUM        repolens/models.py
                                      Filename matches standard 'models.py'
  Services / Logic      HIGH          repolens/engine.py
                                      Central workflow orchestrator
  Tests                 HIGH          tests/test_cli.py (+10 more)
                                      Directory matches 'tests' pattern
------------------------------------------------------------
APPLICATION ENTRY POINTS
  File                  Category      Confidence    Evidence
  repolens/cli.py       CLI           HIGH          Configured as console script 'repolens' in pyproject.toml
------------------------------------------------------------
STRUCTURAL HOTSPOTS (High connectivity / Core coordination)
  Module                Coupling                    Role / Interpretation
  repolens/models.py    24 callers / 0 imports      Foundational module: heavily relied upon across codebase
  repolens/engine.py    1 callers / 11 imports      Orchestrator: aggregates multiple internal subsystems
  repolens/scanner.py   4 callers / 3 imports       Structural nexus: high two-way coordination point
------------------------------------------------------------
RECOMMENDED READING ORDER
  #   File                     Category        Why Read This
  1   README.md                Documentation   Understand project purpose, scope, and user design.
  2   pyproject.toml           Configuration   Inspect dependencies and runnable entry points.
  3   repolens/cli.py          Entry Point     Application starting point (CLI); trace execution wiring.
  4   repolens/models.py       Core Component  Foundational module containing core data representations.
  5   repolens/engine.py       Core Component  Orchestrator aggregating subsystems.
  6   tests/test_cli.py        Verification    Observe expected behavior, arguments, and test contracts.
------------------------------------------------------------
NEXT FILE TO READ: README.md
Understand project purpose, scope, and user design.
------------------------------------------------------------
```

---

## Commands

| Command | Description |
|---|---|
| `repolens [PATH]` | Run full codebase understanding report. |
| `repolens onboard [PATH]` | Generate the "Your First 30 Minutes" contributor onboarding guide. |
| `repolens map [PATH]` | Output dependency graph in Mermaid syntax (or `--format dot`). |
| `repolens hotspots [PATH]` | Display detailed structural dependency hotspot table. |
| `repolens explain <file>` | Inspect a specific file's symbols, callers, and internal dependencies. |
| `repolens scan [PATH]` | Quick filesystem and language discovery pass. |
| `repolens report [PATH] --format json` | Export full machine-readable JSON payload. |

---

## Contributor Onboarding: "Your First 30 Minutes"

Run `repolens onboard` to get an actionable walkthrough:

```bash
repolens onboard .
```

```text
[0-3 min] Project Vision & Problem Statement
  Files to open: README.md
  What to understand: Understand why this project exists and its primary value proposition.

[3-7 min] Application Entry Point & Bootstrap
  Files to open: repolens/cli.py
  What to understand: Understand where execution starts and how command dispatch is initialized.

[7-15 min] Core Workflow & Orchestration
  Files to open: repolens/engine.py
  What to understand: Understand the primary execution lifecycle and how tasks are coordinated.

[15-22 min] Domain Models & Core Entities
  Files to open: repolens/models.py
  What to understand: Understand primary data representations, contracts, and state structures.

[22-27 min] Supporting Infrastructure & Utilities
  Files to open: repolens/discovery/scanner.py, repolens/graph/resolver.py
  What to understand: Understand foundational helper logic and import resolution.

[27-30 min] Test Contracts & Behavior Verification
  Files to open: tests/test_security.py, tests/test_cli.py
  What to understand: Understand how behaviors are verified and how to write a test before opening a PR.
```

---

## Supported Languages

| Language | AST Symbol Extraction | Import / Dependency Graph | Entry-Point Detection |
|---|:---:|:---:|:---:|
| **Python** | ✅ Full AST (`ast` stdlib) | ✅ Relative & Absolute | ✅ High (`__main__`, CLI decorators) |
| **JavaScript** | ✅ Full AST (`tree-sitter`) | ✅ ES Modules & CommonJS | ✅ High (`package.json`, servers) |
| **TypeScript / TSX** | ✅ Full AST (`tree-sitter`) | ✅ ES Modules & CommonJS | ✅ High (`package.json`, servers) |
| **Other Languages** | ⚠️ Structural Fallback | ⚠️ Regex Pattern Detection | ⚠️ Heuristic |

*For unsupported languages (Go, Rust, Java, C++, C#, etc.), RepoLens provides file discovery, language metrics, and regex imports, accompanied by a transparent disclaimer: `"Structural analysis is limited for this language."`*

---

## Security & Privacy Model

- **Zero Untrusted Code Execution**: RepoLens treats every scanned repository as untrusted input. It never runs `eval()`, `exec()`, `importlib`, setup scripts, or package installers.
- **Air-Gapped & Local-First**: RepoLens initiates zero network connections. No telemetry, no pings, no cloud uploads.
- **Resource Protection**: Skips individual files $> 2$ MB for AST parsing and detects binary files via byte inspection.

---

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Competitive Research](docs/COMPETITIVE_RESEARCH.md)
- [Known Limitations](docs/LIMITATIONS.md)
- [Project Roadmap](docs/ROADMAP.md)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)


---

## License

RepoLens is licensed under the [MIT License](LICENSE).
