# Limitations of RepoLens

To maintain high engineering integrity, RepoLens is explicit about what static analysis can and cannot achieve.

---

## Known Boundaries & Limitations

### 1. Static vs. Runtime Execution
RepoLens operates strictly as a static code analyzer and **never executes user repository code**. Consequently:
* **Dynamic Imports**: Imports constructed via strings at runtime (e.g., `importlib.import_module(var_name)` in Python, or `require(computed_path)` in Node.js) cannot be fully resolved to concrete target files. These appear as unresolved dependencies.
* **Metaprogramming & Reflection**: Frameworks that dynamically register functions or generate routes via runtime reflection (such as Django dynamic model attributes, Flask blueprint registries, or NestJS reflection decorators) are detected by pattern heuristics, not by runtime execution.
* **No Runtime Call-Graph Tracing**: RepoLens reports import-level and module-level dependency relationships. It does not trace line-by-line runtime stack traces or execution call trees in V1.

### 2. Monorepos & Path Aliasing
* TypeScript projects utilizing custom `compilerOptions.paths` in `tsconfig.json` (such as `@components/*` or `~/*`) may not resolve to concrete source files if custom root mappings are deeply nested across multiple packages in a monorepo.

### 3. Generated Code
* Code generated automatically by build tools (e.g., Protobuf/gRPC stubs, OpenAPI client SDKs, ORM migration files) can inflate file counts and symbol density. While RepoLens ignores standard directories (`dist`, `build`, `target`), custom generated directories must be ignored via `.gitignore` or custom ignore parameters.

### 4. Architecture Layer Inference
* Architecture layers are **inferred based on observable evidence** (directory conventions, framework imports, caller patterns). These inferences represent likely architectural roles, not formal mathematical proofs.

### 5. Unsupported Languages
* For languages other than Python, JavaScript, and TypeScript (e.g., Go, Rust, Java, C++, C#), RepoLens provides safe structural metrics (file counts, directory hierarchy, basic imports if detected), but displays:
  > *"Structural analysis is limited for this language."*
* Deep AST symbol extraction for these languages is scheduled for future releases.
