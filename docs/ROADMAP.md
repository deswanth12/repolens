# RepoLens Roadmap

RepoLens follows a disciplined, phased evolution. We prioritize deterministic evidence and CLI excellence before adding visualization or AI.

---

## Version 1.0 (Current Release)
- [x] Local-first, zero-config CLI (`repolens .`)
- [x] Filesystem discovery with `.gitignore` and default ignore rules
- [x] Language detection and file categorization (`source`, `test`, `doc`, `config`)
- [x] Python AST parsing using standard library `ast`
- [x] JavaScript, TypeScript, and TSX AST parsing via `tree-sitter`
- [x] Fallback analyzer for unsupported languages with transparent limitations
- [x] Directed module dependency graph with cycle detection
- [x] Evidence-based entry point detection (AST guards, CLI decorators, packaging manifests)
- [x] Structural hotspot detection without vanity scores
- [x] Inferred architectural layer categorization
- [x] Recommended reading order with explicit file rationales
- [x] "Your First 30 Minutes" contributor onboarding blueprint (`repolens onboard`)
- [x] File explainer (`repolens explain <path>`)
- [x] Dependency diagram generation (Mermaid and DOT)
- [x] Machine-readable JSON export (`repolens report . --format json`)

---

## Version 2.0 (Planned)
- [ ] Native AST parsing for Go, Rust, Java, and C#
- [ ] Git history analysis: correlating historical churn with structural hotspots
- [ ] Call-graph extraction (function-level caller/callee links within modules)
- [ ] Path alias resolver for monorepos (`tsconfig.json` paths and `sys.path` hooks)

---

## Version 3.0 (Planned)
- [ ] Local-only, air-gapped LLM reasoning layer (e.g., via Ollama or local ONNX)
- [ ] Grounded natural-language explanations strictly bound to extracted AST facts
- [ ] High-level data flow question answering ("Where does authentication happen?")

---

## Version 4.0 (Planned)
- [ ] GitHub Action: automatic PR architectural impact analysis
- [ ] VS Code Extension: interactive sidebar showing reading order and entry points
- [ ] Model Context Protocol (MCP) server for local IDE coding agents

---

## Version 5.0 (Planned)
- [ ] Interactive local architecture visualizer (`repolens serve`)
- [ ] Architecture drift detection (tracking changes in architectural layers over time)
