# Security Policy

## Security Model & Guarantees

RepoLens is built with a **strict zero-execution security model**:

1. **Zero Execution of Repository Code**:
   - RepoLens never runs `eval()`, `exec()`, or Python module imports (`importlib`, `__import__`) on analyzed files.
   - RepoLens never executes repository scripts (`setup.py`, `package.json` scripts, Makefiles, shell scripts, or test runners).
   - All analysis is performed statically using AST parsing (`ast` standard library in Python, `tree-sitter` for JavaScript/TypeScript).
2. **Local-First & Air-Gapped**:
   - RepoLens makes zero network connections.
   - No telemetry, no usage metrics, no tracking, and no external API requests are made.
   - Code never leaves your local machine.
3. **Path Traversal Protection**:
   - Symlinks and paths attempting to escape the target repository root are checked and isolated.
4. **Denial-of-Service Protection**:
   - Single files larger than 2 MB are skipped for line counting and AST parsing to prevent memory exhaustion on giant blobs.
   - Binary files are detected via null-byte inspection and extension matching, preventing parser crashes.

## Reporting a Vulnerability

If you discover a security vulnerability in RepoLens, please report it privately:

- **Email**: `security@repolens.dev` (or open a confidential GitHub Security Advisory)
- Please provide details on the issue, a minimal reproducing repository, and your platform.
- We will acknowledge receipt within 48 hours and work on a patch before public disclosure.
