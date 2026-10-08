"""JavaScript and TypeScript AST analyzer for RepoLens.

Uses tree-sitter for fast, resilient, static AST parsing without code execution.
Includes fallback regex extraction if parsing is interrupted.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from repolens.analyzers.base import BaseAnalyzer
from repolens.models import (
    FileCategory,
    FileRecord,
    ImportRecord,
    ModuleAnalysis,
    SymbolRecord,
    SymbolType,
)

try:
    import tree_sitter
    import tree_sitter_javascript
    import tree_sitter_typescript

    _JS_LANG = tree_sitter.Language(tree_sitter_javascript.language())
    _TS_LANG = tree_sitter.Language(tree_sitter_typescript.language_typescript())
    _TSX_LANG = tree_sitter.Language(tree_sitter_typescript.language_tsx())
    TREE_SITTER_AVAILABLE = True
except Exception:
    TREE_SITTER_AVAILABLE = False


def _clean_quotes(text: str) -> str:
    """Strips quotes from import string literal."""
    return text.strip("'\"`")


def _node_text(node: Any) -> str:
    """Safely extracts UTF-8 string from a tree-sitter node."""
    if node is not None and getattr(node, "text", None) is not None:
        raw = node.text
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
    return ""


class JavaScriptTypeScriptAnalyzer(BaseAnalyzer):
    """Analyzes JavaScript and TypeScript files."""

    @property
    def language_name(self) -> str:
        return "JavaScript/TypeScript"

    def can_analyze(self, file_record: FileRecord) -> bool:
        return (
            file_record.language in {"JavaScript", "TypeScript"}
            and file_record.category in {FileCategory.SOURCE, FileCategory.TEST}
            and not file_record.is_binary
        )

    def analyze(self, file_path: Path, rel_path: str) -> ModuleAnalysis:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ModuleAnalysis(
                rel_path=rel_path,
                language="TypeScript" if file_path.suffix in {".ts", ".tsx"} else "JavaScript",
                parse_error=f"Could not read file: {e}",
            )

        lang = "TypeScript" if file_path.suffix in {".ts", ".tsx", ".mts", ".cts"} else "JavaScript"

        if TREE_SITTER_AVAILABLE:
            try:
                return self._analyze_with_tree_sitter(content, file_path.suffix, rel_path, lang)
            except Exception:
                # Fallback to regex analysis if AST walk encounters unexpected error
                pass

        return self._analyze_with_regex(content, rel_path, lang)

    def _analyze_with_tree_sitter(
        self, content: str, ext: str, rel_path: str, lang: str
    ) -> ModuleAnalysis:
        raw_bytes = content.encode("utf-8")
        if ext in {".tsx", ".jsx"}:
            parser_lang = _TSX_LANG if ext == ".tsx" else _JS_LANG
        elif ext in {".ts", ".mts", ".cts"}:
            parser_lang = _TS_LANG
        else:
            parser_lang = _JS_LANG

        parser = tree_sitter.Parser(parser_lang)
        tree = parser.parse(raw_bytes)
        root = tree.root_node

        symbols: list[SymbolRecord] = []
        imports: list[ImportRecord] = []
        exports: list[str] = []
        has_main_block = False

        for node in root.children:
            node_type = node.type

            # 1. ES Import statement: import { x } from './y'
            if node_type == "import_statement":
                source_node = None
                imported_names: list[str] = []

                for child in node.children:
                    if child.type in {"string", "string_fragment"}:
                        source_node = child
                    elif child.type == "import_clause":
                        for clause_child in child.children:
                            if clause_child.type == "identifier":
                                imported_names.append(_node_text(clause_child))
                            elif clause_child.type == "named_imports":
                                for spec in clause_child.children:
                                    if spec.type == "import_specifier":
                                        name = spec.child_by_field_name("name") or spec.children[0]
                                        imported_names.append(_node_text(name))

                if source_node:
                    module_name = _clean_quotes(_node_text(source_node))
                    level = 1 if module_name.startswith("./") else (2 if module_name.startswith("../") else 0)
                    imports.append(
                        ImportRecord(
                            module=module_name,
                            imported_names=imported_names,
                            is_from=True,
                            level=level,
                            line_number=node.start_point[0] + 1,
                        )
                    )

            # 2. ES Export statement: export function foo(), export default ...
            elif node_type == "export_statement":
                for child in node.children:
                    if child.type == "function_declaration":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            fname = _node_text(name_node)
                            exports.append(fname)
                            symbols.append(
                                SymbolRecord(
                                    name=fname,
                                    symbol_type=SymbolType.FUNCTION,
                                    line_number=child.start_point[0] + 1,
                                    end_line_number=child.end_point[0] + 1,
                                )
                            )
                    elif child.type == "class_declaration":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            cname = _node_text(name_node)
                            exports.append(cname)
                            symbols.append(
                                SymbolRecord(
                                    name=cname,
                                    symbol_type=SymbolType.CLASS,
                                    line_number=child.start_point[0] + 1,
                                    end_line_number=child.end_point[0] + 1,
                                )
                            )
                    elif child.type == "export_clause":
                        for spec in child.children:
                            if spec.type == "export_specifier":
                                name = spec.child_by_field_name("name") or spec.children[0]
                                exports.append(_node_text(name))

            # 3. Functions
            elif node_type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    fname = _node_text(name_node)
                    is_async = any(c.type == "async" for c in node.children)
                    symbols.append(
                        SymbolRecord(
                            name=fname,
                            symbol_type=SymbolType.ASYNC_FUNCTION if is_async else SymbolType.FUNCTION,
                            line_number=node.start_point[0] + 1,
                            end_line_number=node.end_point[0] + 1,
                        )
                    )

            # 4. Classes
            elif node_type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    cname = _node_text(name_node)
                    bases: list[str] = []
                    heritage = node.child_by_field_name("heritage")
                    if heritage:
                        bases.append(_node_text(heritage))

                    symbols.append(
                        SymbolRecord(
                            name=cname,
                            symbol_type=SymbolType.CLASS,
                            line_number=node.start_point[0] + 1,
                            end_line_number=node.end_point[0] + 1,
                            base_classes=bases,
                        )
                    )

                    body = node.child_by_field_name("body")
                    if body:
                        for item in body.children:
                            if item.type == "method_definition":
                                mname_node = item.child_by_field_name("name")
                                if mname_node:
                                    mname = _node_text(mname_node)
                                    symbols.append(
                                        SymbolRecord(
                                            name=mname,
                                            symbol_type=SymbolType.METHOD,
                                            line_number=item.start_point[0] + 1,
                                            end_line_number=item.end_point[0] + 1,
                                            parent_symbol=cname,
                                        )
                                    )

        # Check for server or CLI execution patterns in text
        if re.search(r"\b(app|server)\.listen\(", content) or re.search(r"require\.main\s*===\s*module", content) or re.search(r"\bprogram\.parse\(", content):
            has_main_block = True

        return ModuleAnalysis(
            rel_path=rel_path,
            language=lang,
            symbols=symbols,
            imports=imports,
            exports=exports,
            has_main_block=has_main_block,
        )

    def _analyze_with_regex(self, content: str, rel_path: str, lang: str) -> ModuleAnalysis:
        """Fallback regex extraction for JS/TS."""
        symbols: list[SymbolRecord] = []
        imports: list[ImportRecord] = []
        exports: list[str] = []

        # Match ES import: import ... from '...'
        for m in re.finditer(r"""import\s+(?:(?:\{([^}]+)\}|\*\s+as\s+(\w+)|(\w+))\s+from\s+)?['"]([^'"]+)['"]""", content):
            module_name = m.group(4)
            names: list[str] = []
            if m.group(1):
                names.extend([n.strip().split()[0] for n in m.group(1).split(",") if n.strip()])
            if m.group(2):
                names.append(m.group(2))
            if m.group(3):
                names.append(m.group(3))
            level = 1 if module_name.startswith("./") else (2 if module_name.startswith("../") else 0)
            imports.append(
                ImportRecord(
                    module=module_name,
                    imported_names=names,
                    is_from=True,
                    level=level,
                )
            )

        # Match CommonJS require: const x = require('...')
        for m in re.finditer(r"""require\(['"]([^'"]+)['"]\)""", content):
            module_name = m.group(1)
            level = 1 if module_name.startswith("./") else (2 if module_name.startswith("../") else 0)
            imports.append(
                ImportRecord(
                    module=module_name,
                    is_from=False,
                    level=level,
                )
            )

        # Match functions
        for m in re.finditer(r"""(?:async\s+)?function\s+(\w+)\s*\(""", content):
            fname = m.group(1)
            symbols.append(
                SymbolRecord(
                    name=fname,
                    symbol_type=SymbolType.FUNCTION,
                    line_number=1,
                    end_line_number=1,
                )
            )

        # Match classes
        for m in re.finditer(r"""class\s+(\w+)(?:\s+extends\s+(\w+))?""", content):
            cname = m.group(1)
            bases = [m.group(2)] if m.group(2) else []
            symbols.append(
                SymbolRecord(
                    name=cname,
                    symbol_type=SymbolType.CLASS,
                    line_number=1,
                    end_line_number=1,
                    base_classes=bases,
                )
            )

        has_main_block = bool(
            re.search(r"\b(app|server)\.listen\(", content)
            or re.search(r"require\.main\s*===\s*module", content)
        )

        return ModuleAnalysis(
            rel_path=rel_path,
            language=lang,
            symbols=symbols,
            imports=imports,
            exports=exports,
            has_main_block=has_main_block,
        )
