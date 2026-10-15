# Security Policy

## Security Model & Guarantees

RepoLens is built with a **strict zero-execution, local-first security model**:

### 1. Zero Execution of Repository Code
- RepoLens never calls `eval()`, `exec()`, or Python module imports (`importlib`, `__import__`) on analyzed files.
- RepoLens never executes repository build scripts (`setup.py`, `package.json` scripts, Makefiles, shell scripts, or test runners).
- All source analysis is performed statically using AST parsing (`ast` standard library in Python, `tree-sitter` for JavaScript/TypeScript, and structural regex for unsupported fallbacks).

### 2. Local-First & Air-Gapped Privacy
- RepoLens initiates zero external network connections.
- No telemetry, no usage metrics, no tracking pings, and no cloud LLM API requests are made.
- Scanned repository code never leaves your local machine.

### 3. Path Traversal & Symlink Isolation
- **File Symlinks**: Every discovered file symlink has its canonical target resolved (`resolve(strict=True)`). If the canonical path points outside the repository root, it is rejected immediately, excluded from analysis, and logged in scan warnings.
- **Directory Symlinks**: Directory symlinks are pruned during filesystem traversal to prevent infinite recursion loops and unauthorized root escapes.
- **Broken / Non-File Symlinks**: Broken symlinks, socket symlinks, or FIFO symlinks are safely skipped without crashing.

### 4. Denial-of-Service & Resource Protections
- **Oversized Files**: Files larger than **2 MiB (2,097,152 bytes)** are skipped for line counting and AST parsing. The engine records a clean `parse_error` noting the skip reason rather than loading the file into memory.
- **Binary Files**: Binary files are detected via known binary extension tables and 1,024-byte null-byte inspection (`\x00`). Binary files are classified as `OTHER` and never sent to AST parsers.
- **Dependency Recursion**: Graph cycle detection uses an iterative depth-first search (DFS) with explicit heap-allocated stacks, preventing Python `RecursionError` crashes on arbitrarily deep dependency chains (e.g. 3,000+ nodes).

### 5. Explicit Security Boundaries (What RepoLens Does Not Do)
- **Secret Scanning**: RepoLens excludes common sensitive filenames (`.env`, `*.pem`, `*.key`, `id_rsa`) from reading, but it is **not** a dedicated secret-detection scanner (e.g. GitGuardian, Trufflehog) and does not scan source code bodies for high-entropy secrets or API tokens.
- **Dynamic Analysis**: RepoLens cannot resolve runtime-dynamically generated imports (e.g. `importlib.import_module(var)`) and marks unresolved relationships accordingly.

---

## Reporting a Vulnerability

If you discover a security vulnerability in RepoLens, please report it privately:

- **Email**: `security@repolens.dev` (or open a confidential GitHub Security Advisory on `deswanth12/repolens`)
- Please include:
  - A description of the issue.
  - A minimal reproducing repository or test fixture.
  - Operating system and Python version.
- We will acknowledge receipt within 48 hours and coordinate a validated patch before public release.
