# RepoLens — Launch & Feedback Kit

This kit contains verified launch messaging, quick demonstration scripts, feedback templates, and outreach material for RepoLens v0.1.0.

---

## 1. One-Sentence Description

**RepoLens** is a local-first, zero-execution static analysis CLI that helps developers understand unfamiliar codebases through entry-point detection, dependency mapping, structural hotspots, and contributor onboarding roadmaps.

---

## 2. Target Audience & The Problem It Solves

### Target Audience
- **Open-source contributors and maintainers**: Developers onboarding onto new open-source projects or structuring onboarding paths for first-time contributors.
- **Software engineers joining new teams**: Engineers tasked with understanding unfamiliar legacy or multi-module repositories without waiting for senior engineering walkthroughs.
- **Code reviewers & tech leads**: Architects needing deterministic visibility into internal coupling, entry points, and structural hotspots before approving large refactors.
- **Students & educators**: Learners exploring real-world codebases to see how software architecture and design patterns look in production.

### The Problem It Solves
When opening a new codebase, developers ask:
- *"Where does this application actually start?"*
- *"Which files are foundational models vs. workflow orchestrators?"*
- *"Which files should I read first, in what order, and why?"*
- *"What should I focus on during my first 30 minutes with this project?"*

Existing tools either point out syntax flaws (`ruff`, `eslint`), draw unreadable spiderwebs of hundreds of edges (`madge`), require prior knowledge of architecture rules (`import-linter`), or send proprietary source code to cloud LLM prompts.

RepoLens answers these questions locally and deterministically using AST parsing and repository evidence.

---

## 3. Three Evidence-Backed Product Differentiators

1. **Zero Execution, Air-Gapped Security**
   - Treats analyzed code strictly as untrusted input.
   - Never invokes `eval()`, `exec()`, `importlib`, setup scripts, or package managers.
   - 100% offline with zero network requests, zero external API keys, and zero telemetry.

2. **Actionable Contributor Onboarding (`repolens onboard`)**
   - Breaks repo onboarding into a time-boxed 30-minute roadmap:
     - `0–3 min`: Vision & Problem Statement (`README.md`, `CONTRIBUTING.md`)
     - `3–7 min`: Application Entry Point & Bootstrap (`cli.py`, `main.py`)
     - `7–15 min`: Core Workflow & Orchestration
     - `15–22 min`: Domain Models & Core Entities
     - `22–27 min`: Supporting Infrastructure & Utilities
     - `27–30 min`: Test Contracts & Behavior Verification
   - Every file recommendation includes the explicit reason *why* to read it.

3. **Structural Hotspots Without Defect Scoring**
   - High fan-in and fan-out modules are classified by functional role (Foundational Module, Orchestrator, Structural Nexus, Shared Component) rather than penalized with an arbitrary 0–100 "bad code" score.

---

## 4. 30-Second Demonstration Script

### Step 1: Install
```bash
# Direct install from GitHub release wheel:
pip install https://github.com/deswanth12/repolens/releases/download/v0.1.0/repolens-0.1.0-py3-none-any.whl

# Or install editable from repository:
git clone https://github.com/deswanth12/repolens.git
cd repolens
pip install -e .
```

### Step 2: Run Full Codebase Understanding
```bash
repolens .
```
**Verified Output:**
```text
RepoLens v0.1.0 -- Understand how a codebase works
------------------------------------------------------------
  Project:                repolens
  Primary Language:       Python
  Files (Total / Source): 94 total / 30 source
  Tests / Docs:           44 tests / 14 docs
  Total Lines:            6,145
  Entry Points:           1
------------------------------------------------------------
APPLICATION ENTRY POINTS
  File               Category    Confidence    Evidence
  repolens/cli.py    CLI         HIGH          Configured as executable console script 'repolens' in pyproject.toml.
------------------------------------------------------------
STRUCTURAL HOTSPOTS (High connectivity / Core coordination)
  Module                     Coupling (In/Out)         Role / Interpretation
  repolens/models.py         26 callers / 0 imports    Foundational module: heavily relied upon across codebase
  repolens/engine.py         3 callers / 12 imports    Orchestrator: aggregates multiple internal subsystems
------------------------------------------------------------
RECOMMENDED READING ORDER
  #  File                Category       Why Read This
  1  README.md           Documentation  Understand project purpose and scope.
  2  pyproject.toml      Configuration  Inspect declared dependencies and entry points.
  3  repolens/cli.py     Entry Point    Application starting point; trace execution kickoff.
  4  repolens/models.py  Core Component Foundational data representations.
  5  repolens/engine.py  Core Component Orchestrator aggregating subsystems.
```

### Step 3: Get the 30-Minute Onboarding Blueprint
```bash
repolens onboard .
```

---

## 5. Short GitHub Announcement

**Title:** RepoLens v0.1.0 — Understand how an unfamiliar codebase works (local-first, zero-execution static analysis)

**Body:**
> Hey everyone! 👋
>
> I've just released **RepoLens v0.1.0**, an open-source CLI built to solve a simple but frustrating problem: *“I just cloned this codebase. Where do I actually start?”*
>
> Instead of drawing 300-node dependency spiderwebs or sending code to external LLMs, RepoLens uses AST parsing (Python stdlib `ast`, JavaScript/TypeScript `tree-sitter`) to deterministically answer:
>
> - 🔍 **Where execution starts** (CLI scripts, `__main__` guards, framework routes)
> - 🧭 **Which files to read first and why** (Recommended sequential reading order)
> - ⏱️ **A 30-minute contributor onboarding blueprint** (`repolens onboard .`)
> - ⚡ **Structural hotspots and architectural layers** without arbitrary quality scoring
>
> It runs 100% locally with zero code execution and zero network calls.
>
> - Repository: https://github.com/deswanth12/repolens
> - Release: https://github.com/deswanth12/repolens/releases/tag/v0.1.0
>
> Try running `repolens onboard .` on your own project. Feedback and bug reports on different repository layouts are very welcome!

---

## 6. Professional LinkedIn Launch Post

```text
Every developer knows the feeling of opening an unfamiliar codebase for the first time:

You open ten tabs, look through directory trees, guess where main() lives, and try to piece together the mental model from scratch.

Existing tools usually fall into two extremes:
1. Linters that tell you about syntax formatting errors.
2. AI tools that send your proprietary repository to cloud APIs and hallucinate file paths.

I built RepoLens to take a different approach: evidence-based, local-first repository understanding.

RepoLens is a Python CLI that inspects repositories statically using AST parsing (Python AST and Tree-Sitter for JS/TS) to produce:
• Identified application entry points with verified confidence levels.
• A 6-step recommended reading order explaining why each file matters.
• A time-boxed 30-minute contributor onboarding guide (run `repolens onboard .`).
• Structural dependency hotspots classified by role (Foundational, Orchestrator, Nexus) without arbitrary 0–100 defect scoring.
• Clean dependency diagrams in Mermaid and DOT formats.

Key guarantees:
✓ Zero execution of repository code (safe on untrusted code).
✓ 100% local and offline (zero telemetry, zero cloud calls).
✓ MIT Licensed.

RepoLens v0.1.0 is now live on GitHub:
https://github.com/deswanth12/repolens

If you maintain or contribute to an open-source project, run `repolens onboard .` on your repo and let me know what you think of the generated reading order!
```

---

## 7. Concise Outreach Message for Open-Source Developers

```text
Hi [Name],

I saw your work on [Project] and love the project.

I recently published RepoLens (https://github.com/deswanth12/repolens), an open-source, local-first CLI that analyzes codebases statically to generate a 30-minute contributor onboarding roadmap (`repolens onboard .`) and an evidence-backed reading order.

It executes zero user code and makes zero network calls.

I'd really value 2 minutes of your feedback: if you run `repolens onboard .` on [Project], does the suggested reading order and entry point match how you would introduce a new contributor to the codebase?

Thanks for your time and for building great open source!
```

---

## 8. Five Useful Questions to Ask First-Time Users

1. **Entry Point Accuracy**: Did RepoLens correctly identify where your application actually starts, or did it miss a custom bootstrap script?
2. **Reading Order Value**: If a junior developer followed the generated 6-file reading order, would they understand your system faster than browsing files manually?
3. **Hotspot Classification**: Did the structural hotspots reflect the actual core modules in your architecture (e.g., domain models vs. workflow coordinators)?
4. **Noise & Filtering**: Did any test fixtures, build artifacts, or vendor directories pollute your architecture or reading order?
5. **Output Usability**: Was the terminal output easy to read on your screen, or did long paths / table columns wrap awkwardly?

---

## 9. Feedback Tracking Template

Use this format when logging user feedback, community bug reports, and enhancement requests:

```markdown
### Feedback Item #[ID]

- **Date Received**: YYYY-MM-DD
- **Source**: [GitHub Issue / LinkedIn / Direct Message / Discussion]
- **Repository Tested**: [Repo Name, Language, Approx. Files]
- **User Role**: [Maintainer / First-time Contributor / Student / Lead Engineer]

#### Observed Problem / Experience
[Description of what the user experienced or found confusing]

#### Reproduction Steps
```bash
repolens [COMMAND] [PATH] [FLAGS]
```

#### Expected vs. Actual Output
- **Expected**: [What the user expected to see]
- **Actual**: [What RepoLens actually reported]

#### Impact
- [ ] Blocker (Crash / Fatal Error / Security Concern)
- [ ] Accuracy Issue (Incorrect entry point / misclassified layer)
- [ ] Noise Issue (Auxiliary files or fixtures included in output)
- [ ] Usability / Formatting (Table wrapping, confusing wording)
- [ ] Feature Request (Additional language / export format)

#### Proposed Next Action
- **Action**: [Specific code change, doc update, or test case needed]
- **Status**: [Investigating / Triaged / In Progress / Resolved]
- **Tracking Reference**: [Commit hash or Issue #]
```
