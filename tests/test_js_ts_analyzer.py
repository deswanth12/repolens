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
    assert "Structural analysis is limited" in (analysis.parse_error or "")
    imported_mods = [i.module for i in analysis.imports]
    assert "fmt" in imported_mods or "net/http" in imported_mods

    rust_path = tmp_path / "lib.rs"
    rust_path.write_text("use std::collections::HashMap;\n", encoding="utf-8")
    rust_analysis = analyzer.analyze(rust_path, "lib.rs")
    assert rust_analysis.language == "Rust"
    assert any("HashMap" in i.module for i in rust_analysis.imports)
