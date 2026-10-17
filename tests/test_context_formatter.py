"""Unit tests for the AI Context Pack formatter (repolens.formatters.context)."""

from pathlib import Path

from repolens.engine import RepoLensEngine
from repolens.formatters.context import format_ai_context


def test_format_ai_context_sections(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo Project\nThis is a demo.\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "\"\"\"Main application module.\"\"\"\n"
        "class App:\n"
        "    \"\"\"Core application class.\"\"\"\n"
        "    pass\n\n"
        "def main():\n"
        "    \"\"\"Start the application.\"\"\"\n"
        "    pass\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )

    engine = RepoLensEngine(tmp_path)
    result = engine.analyze()

    content = format_ai_context(result, include_mermaid=True)

    assert "# Codebase Intelligence:" in content
    assert "## 1. Project Profile & Scale" in content
    assert "## 2. Application Entry Points" in content
    assert "## 3. Inferred Architecture & Layers" in content
    assert "## 4. Architectural Hotspots" in content
    assert "## 5. Recommended Reading Sequence" in content
    assert "## 6. Dependency Map" in content
    assert "```mermaid" in content
    assert "## 7. AI Agent Guardrails & Invariants" in content
    assert "[OK] Zero circular dependencies detected" in content


def test_format_ai_context_no_mermaid(tmp_path: Path):
    (tmp_path / "index.js").write_text("console.log('hello');\n", encoding="utf-8")

    engine = RepoLensEngine(tmp_path)
    result = engine.analyze()

    content = format_ai_context(result, include_mermaid=False)
    assert "## 6. Dependency Map" not in content
    assert "```mermaid" not in content
