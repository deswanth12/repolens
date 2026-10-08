# Contributing to RepoLens

Thank you for your interest in contributing to RepoLens!

RepoLens is built to help developers understand unfamiliar repositories quickly, using **deterministic evidence** rather than speculative scores or external AI calls.

---

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please treat everyone with respect and kindness.

---

## Development Setup

RepoLens is written in Python 3.10+ and requires minimal dependencies:

```bash
# 1. Clone the repository
git clone https://github.com/repolens/repolens.git
cd repolens

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies and RepoLens in editable mode
pip install -e ".[dev]"

# 4. Run the test suite
pytest -v
```

---

## Adding a New Language Analyzer

RepoLens uses a pluggable analyzer architecture:

1. Subclass `BaseAnalyzer` in `repolens/analyzers/`:
   ```python
   from repolens.analyzers.base import BaseAnalyzer
   from repolens.models import FileRecord, ModuleAnalysis

   class MyLanguageAnalyzer(BaseAnalyzer):
       @property
       def language_name(self) -> str:
           return "MyLang"

       def can_analyze(self, file_record: FileRecord) -> bool:
           return file_record.language == "MyLang" and not file_record.is_binary

       def analyze(self, file_path: Path, rel_path: str) -> ModuleAnalysis:
           # Extract symbols, imports, exports statically without executing code!
           ...
   ```
2. Register the analyzer in `repolens/engine.py`.
3. Add a test in `tests/test_mylang_analyzer.py` and a fixture under `tests/fixtures/`.
4. Ensure no code execution occurs during analysis!

---

## Pull Request Guidelines

1. **Keep Pull Requests Focused**: One logical feature or bug fix per PR.
2. **Add Tests**: All new functionality must include tests covering both normal execution and malformed input.
3. **Verify Existing Tests**: Run `pytest -v` to ensure no regressions.
4. **Follow Design Principles**:
   - Evidence over speculation.
   - Deterministic before AI.
   - Zero execution of user repository code.
   - Resilient on Windows, macOS, and Linux terminals.
