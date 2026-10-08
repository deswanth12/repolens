# RepoLens

> **Understand how a codebase works.**

RepoLens is a local-first developer tool that analyzes unfamiliar repositories and builds an evidence-based map of their structure, dependencies, important modules, and recommended reading order.

---

## The Core Problem

> *"I cloned this repository. How does it actually work?"*

RepoLens answers that question using deterministic repository evidence:
- **Where does this application start?**
- **What are the important modules?**
- **Which files depend on which other files?**
- **What are the main architectural layers?**
- **Which files should I read first?**
- **What should a new contributor understand in their first 30 minutes?**

---

## Design Principles

1. **Evidence over speculation**: Every insight cites exact source code or configuration evidence.
2. **Deterministic before AI**: V1 requires zero LLM keys, zero network connections, and operates 100% locally.
3. **No vanity scores**: No arbitrary 0–100 health metrics. We report measured facts.
4. **Zero execution of repository code**: Completely static AST analysis. We never run untrusted repository code.
