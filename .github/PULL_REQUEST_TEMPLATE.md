## Description
Briefly describe the purpose of this change.

## Changes Made
- Point 1
- Point 2

## Testing Performed
- [ ] Added unit or integration tests covering normal and edge cases
- [ ] Ran `pytest -v` across all test suites (all tests passing)
- [ ] Ran `ruff check .` and `ruff format --check .` (0 errors)
- [ ] Ran `mypy repolens` (0 type errors)
- [ ] Tested against sample or fixture repositories

## Security & Principles Checklist
- [ ] Verifiably does not execute user repository code (zero-execution principle)
- [ ] No remote network calls, tracking pings, or external telemetry
- [ ] Adheres to path traversal and symlink boundary limits
- [ ] Respects the 2 MiB file parsing ceiling
- [ ] Gracefully handles syntax errors, circular imports, and unsupported languages
