"""Tests for the JavaScript/TypeScript and Fallback analyzers."""

from pathlib import Path

from repolens.analyzers.fallback_analyzer import FallbackAnalyzer
from repolens.analyzers.js_ts_analyzer import JavaScriptTypeScriptAnalyzer
from repolens.models import FileCategory, FileRecord, SymbolType


def test_js_ts_analyzer_can_analyze():
    analyzer = JavaScriptTypeScriptAnalyzer()
    js_rec = FileRecord("src/index.js", ".js", "JavaScript", FileCategory.SOURCE, 100)
    ts_rec = FileRecord("src/app.ts", ".ts", "TypeScript", FileCategory.SOURCE, 100)
    py_rec = FileRecord("main.py", ".py", "Python", FileCategory.SOURCE, 100)

    assert analyzer.can_analyze(js_rec) is True
    assert analyzer.can_analyze(ts_rec) is True
    assert analyzer.can_analyze(py_rec) is False


def test_ts_analyzer_symbols_and_imports(tmp_path: Path):
    source = """
import { AuthService } from './auth';
import express from 'express';

export class UserController {
    constructor() {}
    public getUser() {
        return "user";
    }
}

export function startServer() {
    const app = express();
    app.listen(3000);
}
"""
    file_path = tmp_path / "server.ts"
    file_path.write_text(source, encoding="utf-8")

    analyzer = JavaScriptTypeScriptAnalyzer()
    analysis = analyzer.analyze(file_path, "server.ts")

    assert analysis.rel_path == "server.ts"
    assert analysis.language == "TypeScript"
    assert analysis.has_main_block is True

    # Imports
    modules = [i.module for i in analysis.imports]
    assert "./auth" in modules
    assert "express" in modules

    # Symbols
    names = {s.name: s for s in analysis.symbols}
    assert "UserController" in names
    assert names["UserController"].symbol_type == SymbolType.CLASS
    assert "startServer" in names
    assert names["startServer"].symbol_type == SymbolType.FUNCTION


def test_fallback_analyzer(tmp_path: Path):
    go_source = """package main

import (
    "fmt"
    "net/http"
)

func main() {
    fmt.Println("hello")
}
"""
    file_path = tmp_path / "main.go"
    file_path.write_text(go_source, encoding="utf-8")

    rec = FileRecord("main.go", ".go", "Go", FileCategory.SOURCE, 100)
    analyzer = FallbackAnalyzer()
    assert analyzer.can_analyze(rec) is True

    analysis = analyzer.analyze(file_path, "main.go")
    assert analysis.language == "Go"
    assert analysis.parse_error is None
    assert analysis.analysis_mode == "regex_fallback"
    assert any("Structural analysis is limited" in w for w in analysis.warnings)
    imported_mods = [i.module for i in analysis.imports]
    assert "fmt" in imported_mods or "net/http" in imported_mods

    rust_path = tmp_path / "lib.rs"
    rust_path.write_text("use std::collections::HashMap;\n", encoding="utf-8")
    rust_analysis = analyzer.analyze(rust_path, "lib.rs")
    assert rust_analysis.language == "Rust"
    assert rust_analysis.parse_error is None
    assert rust_analysis.analysis_mode == "regex_fallback"
    assert any("HashMap" in i.module for i in rust_analysis.imports)


def test_fallback_analyzer_does_not_falsely_extract_cross_language_comments(tmp_path: Path):
    go_source = """package tui
// Note: use click events to handle user actions
import (
    "os"
    "time"
)
"""
    file_path = tmp_path / "tui.go"
    file_path.write_text(go_source, encoding="utf-8")

    analyzer = FallbackAnalyzer()
    analysis = analyzer.analyze(file_path, "tui.go")
    assert analysis.parse_error is None
    imported_mods = [i.module for i in analysis.imports]
    assert "os" in imported_mods
    assert "time" in imported_mods
    assert "click" not in imported_mods


def test_malformed_javascript_produces_parse_warning_or_fallback(tmp_path: Path):
    """Verifies that syntactically broken or malformed JavaScript produces an explicit parse_error warning."""
    malformed_js = """
    import { unbroken } from './safe';
    function unclosed( {
        const x = ;;;
        return
    // Missing brackets and illegal tokens
    """
    file_path = tmp_path / "broken.js"
    file_path.write_text(malformed_js, encoding="utf-8")

    analyzer = JavaScriptTypeScriptAnalyzer()
    analysis = analyzer.analyze(file_path, "broken.js")

    assert analysis.rel_path == "broken.js"
    assert analysis.language == "JavaScript"
    # Even on malformed syntax, the analyzer safely records parse_error and doesn't crash
    assert analysis.parse_error is not None
    assert "Syntax error" in analysis.parse_error or "regex fallback" in analysis.parse_error
    # And resiliently extracts valid imports if present
    assert any(i.module == "./safe" for i in analysis.imports)


def test_valid_file_analyzed_with_regex_fallback_has_no_parse_error(tmp_path: Path):
    """Verifies that a valid JS file analyzed via regex fallback mode has parse_error=None and analysis_mode='regex_fallback'."""
    valid_js = """
    import { Router } from 'express';
    import { helper } from './utils';

    export class ApiRouter {
        constructor() {}
    }

    export function createServer() {
        return true;
    }
    """
    file_path = tmp_path / "valid.js"
    file_path.write_text(valid_js, encoding="utf-8")

    analyzer = JavaScriptTypeScriptAnalyzer()
    # Explicitly test the regex fallback pathway
    analysis = analyzer._analyze_with_regex(valid_js, "valid.js", "JavaScript")

    assert analysis.rel_path == "valid.js"
    assert analysis.language == "JavaScript"
    assert analysis.analysis_mode == "regex_fallback"
    assert analysis.parse_error is None, "Regex fallback on valid source must NOT be marked as a parse error!"
    assert len(analysis.warnings) >= 1
    assert "regex fallback" in analysis.warnings[0].lower()
    assert any(i.module == "express" for i in analysis.imports)
    assert any(i.module == "./utils" for i in analysis.imports)
    assert any(s.name == "ApiRouter" for s in analysis.symbols)
    assert any(s.name == "createServer" for s in analysis.symbols)


