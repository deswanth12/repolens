# Competitive Research: Codebase Understanding & Visualization Ecosystem

This document evaluates the existing developer tool ecosystem to answer the core strategic question:

> **"Why should RepoLens exist when these tools already exist?"**

---

## Competitor Landscape Overview

Tools in this space broadly fall into six categories:
1. **Module Dependency Visualizers & Linters** (`Madge`, `dependency-cruiser`, `pydeps`, `import-linter`)
2. **UML & Class Structure Generators** (`Pyreverse` / Pylint)
3. **Behavioral Code Analysis & Churn Hotspots** (`CodeScene`, `code-maat`)
4. **Interactive Codebase Navigators** (`Sourcetrail`, `CodeSee`)
5. **AI Context Packagers & AI Assistants** (`Repomix`, `Aider repo-map`, `RepoMind`)
6. **Code Indexing Protocols** (Sourcegraph `SCIP`, LSIF)

---

## Detailed Competitor Breakdown

### 1. Madge
* **Repository**: [`https://github.com/pahen/madge`](https://github.com/pahen/madge)
* **Stack**: JavaScript / TypeScript (Node.js)
* **Popularity**: ~4.8k GitHub stars | Active
* **Purpose**: Generates visual dependency graphs and detects circular dependencies in JS/TS projects.
* **Strengths**: Fast at detecting circular imports; simple CLI export to Graphviz/SVG.
* **Weaknesses**: Produces unpruned, cluttered graph diagrams on non-trivial repos; limited strictly to JS/TS; provides zero architectural synthesis, entry-point reasoning, or reading guidance.

### 2. dependency-cruiser
* **Repository**: [`https://github.com/sverweij/dependency-cruiser`](https://github.com/sverweij/dependency-cruiser)
* **Stack**: JavaScript / TypeScript
* **Popularity**: ~5.5k GitHub stars | Highly active
* **Purpose**: Rule-based architectural validation and dependency graph generation for JS/TS.
* **Strengths**: Comprehensive rule validation engine for CI/CD; detects missing dependencies in `package.json`.
* **Weaknesses**: Requires you to *already understand the architecture* to write custom rules; outputs raw graph dumps; does not provide developer onboarding or reading order.

### 3. pydeps
* **Repository**: [`https://github.com/thebjorn/pydeps`](https://github.com/thebjorn/pydeps)
* **Stack**: Python
* **Popularity**: ~1.7k GitHub stars | Active
* **Purpose**: Python module dependency graph visualizer using Graphviz.
* **Strengths**: Good at filtering standard library modules; includes "Bacon number" distance calculation.
* **Weaknesses**: Requires Graphviz installed on the system; outputs large, hard-to-read image files; no AST symbol extraction or contributor onboarding insights.

### 4. Sourcetrail
* **Repository**: [`https://github.com/CoatiSoftware/Sourcetrail`](https://github.com/CoatiSoftware/Sourcetrail)
* **Stack**: C++, Java, Python (Desktop GUI)
* **Popularity**: ~13k GitHub stars | **Archived / Discontinued in 2021**
* **Purpose**: Interactive graphical code exploration tool with an infinite canvas for symbols and call graphs.
* **Strengths**: High-fidelity symbol cross-referencing and interactive visual navigation.
* **Weaknesses**: Abandoned open-source project; required heavyweight desktop GUI and complex project compilation indexing; cannot run as a fast terminal CLI on a remote server or container.

### 5. Aider (repo-map component)
* **Repository**: [`https://github.com/paul-gauthier/aider`](https://github.com/paul-gauthier/aider)
* **Stack**: Python / Tree-sitter
* **Popularity**: ~25k+ GitHub stars | Highly active
* **Purpose**: Extracts symbol signatures and runs PageRank over references to construct a compact repository map for LLM prompt context.
* **Strengths**: Excellent at selecting high-leverage symbols to fit inside token budgets.
* **Weaknesses**: Built exclusively as an LLM editing aid, not as a standalone developer onboarding or understanding tool; does not produce human-readable architecture layers or reading paths.

### 6. Import Linter
* **Repository**: [`https://github.com/seddonym/import-linter`](https://github.com/seddonym/import-linter)
* **Stack**: Python
* **Popularity**: ~850 GitHub stars | Active
* **Purpose**: Enforces architectural layer contracts between Python packages.
* **Strengths**: Clean contract syntax (e.g., "layer A may not import layer B"); includes browser graph viewer.
* **Weaknesses**: Focuses on asserting pre-existing rules rather than discovering unfamiliar codebases; does not infer architecture or provide reading recommendations.

### 7. Pyreverse (part of Pylint)
* **Repository**: Included in [`https://github.com/pylint-dev/pylint`](https://github.com/pylint-dev/pylint)
* **Stack**: Python
* **Popularity**: ~9.5k GitHub stars (Pylint) | Active
* **Purpose**: Reverse-engineers Python source code into UML class and package diagrams (PlantUML, DOT, Mermaid).
* **Strengths**: Native part of Pylint; extracts class hierarchies and inheritance.
* **Weaknesses**: Strictly object-oriented UML diagram focus; no execution entry-point detection, data flow synthesis, or onboarding walkthrough.

### 8. Repomix (formerly Repopack)
* **Repository**: [`https://github.com/yamadashy/repomix`](https://github.com/yamadashy/repomix)
* **Stack**: TypeScript / Node.js
* **Popularity**: ~9k+ GitHub stars | Highly active
* **Purpose**: Packs an entire repository into a single AI-friendly XML/Markdown file for feeding into LLMs.
* **Strengths**: Respects `.gitignore`; easy prompt packaging for Claude or ChatGPT.
* **Weaknesses**: Dumps raw unanalyzed file text; performs zero AST relationship mapping or internal structure synthesis; requires sending code to external LLMs.

### 9. CodeSee Map Action
* **Repository**: [`https://github.com/Codesee-io/codesee-map-action`](https://github.com/Codesee-io)
* **Stack**: TypeScript / SaaS
* **Popularity**: ~800 GitHub stars | **Discontinued / Dormant SaaS**
* **Purpose**: Cloud-rendered visual architecture maps and PR impact diagrams.
* **Strengths**: Visually polished web diagrams.
* **Weaknesses**: Cloud SaaS lock-in; required proprietary accounts; discontinued core service.

### 10. CodeScene / code-maat
* **Repository**: [`https://github.com/adamtornhill/code-maat`](https://github.com/adamtornhill/code-maat) & Commercial
* **Stack**: Clojure / Python
* **Popularity**: ~2.5k GitHub stars (code-maat) | Active Commercial
* **Purpose**: Behavioral code analysis correlating Git commit history with cyclomatic complexity to identify maintenance hotspots.
* **Strengths**: Data-driven technical debt prioritization based on developer churn.
* **Weaknesses**: Requires extensive historical Git commit logs; commercial paywall; answers *"what needs refactoring?"* rather than *"I just cloned this today: what does it do and what do I read first?"*

---

## Summary Matrix

| Tool | Focus | Zero-Config CLI | Supported Languages | Deterministic | Guided Reading Order | 30-Min Onboarding Flow |
|---|---|:---:|---|:---:|:---:|:---:|
| **Madge** | Circular imports | Yes | JS / TS | Yes | No | No |
| **dependency-cruiser** | Architecture lint | No | JS / TS | Yes | No | No |
| **pydeps** | Graphviz dependency | Yes | Python | Yes | No | No |
| **Sourcetrail** | Symbol search GUI | No | C++, Java, Py | Yes | No | No |
| **Aider (repo-map)**| LLM prompt context | No | Polyglot | Probabilistic | No | No |
| **Import Linter** | Contract checking | No | Python | Yes | No | No |
| **Pyreverse** | UML class diagrams | Yes | Python | Yes | No | No |
| **Repomix** | LLM prompt dumper | Yes | Polyglot | N/A | No | No |
| **CodeScene** | Refactoring debt | No | Polyglot | Yes | No | No |
| **RepoLens** | **Codebase Understanding** | **Yes** | **Python, JS, TS** | **Yes** | **Yes** | **Yes** |

---

## Why RepoLens Exists

RepoLens fills a critical void:

1. **Focus on Understanding, Not Auditing**:  
   Existing tools are linters that tell you what you did wrong (`dependency-cruiser`, `import-linter`), or raw visualizers that output overwhelming 300-node graph hairballs (`madge`, `pydeps`). RepoLens synthesizes findings into human-oriented mental models.
2. **The "Where Do I Start?" Problem**:  
   RepoLens is the only tool that extracts evidence-backed entry points and generates a prioritized, 6-step reading roadmap explaining *why* each file matters.
3. **The 30-Minute Contributor Onboarding Flow**:  
   With `repolens onboard`, new contributors and code reviewers get an instant, phased guide to the repository's vision, bootstrap, workflow, domain models, infrastructure, and tests.
4. **Deterministic & Local-First**:  
   RepoLens requires no API keys, no network connections, and no proprietary accounts. It provides verifiable, reproducible answers based purely on repository source code.
