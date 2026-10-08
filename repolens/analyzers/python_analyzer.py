"""Python AST analyzer for RepoLens.

Uses the Python standard library 'ast' module for 100% deterministic,
safe, local-only AST extraction. Never executes any source code.
"""

from __future__ import annotations

import ast
from pathlib import Path

from repolens.analyzers.base import BaseAnalyzer
from repolens.models import (
    FileCategory,
    FileRecord,
    ImportRecord,
    ModuleAnalysis,
    SymbolRecord,
    SymbolType,
)


def _format_expr(node: ast.AST | None) -> str:
    """Helper to convert AST expression into a readable string (e.g. for decorators, bases)."""
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value_str = _format_expr(node.value)
        return f"{value_str}.{node.attr}" if value_str else node.attr
    if isinstance(node, ast.Call):
        return _format_expr(node.func)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ""


def _is_main_check(node: ast.If) -> bool:
    """Checks if an if statement is 'if __name__ == "__main__":'."""
    test = node.test
    if not isinstance(test, ast.Compare):
        return False

    # Check for == operator
    if not any(isinstance(op, ast.Eq) for op in test.ops):
        return False

    def is_name_main(expr: ast.AST) -> bool:
        return isinstance(expr, ast.Name) and expr.id == "__name__"

    def is_str_main(expr: ast.AST) -> bool:
        return isinstance(expr, ast.Constant) and expr.value == "__main__"

    # Compare left and comparators
    left_is_name = is_name_main(test.left)
    left_is_str = is_str_main(test.left)

    for comparator in test.comparators:
        if left_is_name and is_str_main(comparator):
            return True
        if left_is_str and is_name_main(comparator):
            return True

    return False


class PythonAnalyzer(BaseAnalyzer):
    """Analyzes Python source files using standard library AST parsing."""

    @property
    def language_name(self) -> str:
        return "Python"

    def can_analyze(self, file_record: FileRecord) -> bool:
        return (
            file_record.language == "Python"
            and file_record.category in {FileCategory.SOURCE, FileCategory.TEST}
            and not file_record.is_binary
        )

    def analyze(self, file_path: Path, rel_path: str) -> ModuleAnalysis:
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ModuleAnalysis(
                rel_path=rel_path,
                language="Python",
                parse_error=f"Could not read file: {e}",
            )

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            return ModuleAnalysis(
                rel_path=rel_path,
                language="Python",
                parse_error=f"Syntax error at line {e.lineno}: {e.msg}",
            )
        except Exception as e:
            return ModuleAnalysis(
                rel_path=rel_path,
                language="Python",
                parse_error=f"Parse failed: {e}",
            )

        symbols: list[SymbolRecord] = []
        imports: list[ImportRecord] = []
        exports: list[str] = []
        has_main_block = False

        for node in tree.body:
            # 1. Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportRecord(
                            module=alias.name,
                            imported_names=[],
                            alias=alias.asname,
                            is_from=False,
                            level=0,
                            line_number=node.lineno,
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                names = [a.name for a in node.names]
                imports.append(
                    ImportRecord(
                        module=module_name,
                        imported_names=names,
                        alias=None,
                        is_from=True,
                        level=node.level or 0,
                        line_number=node.lineno,
                    )
                )

            # 2. Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = [_format_expr(d) for d in node.decorator_list if _format_expr(d)]
                docstring = ast.get_docstring(node)
                first_doc_line = docstring.strip().splitlines()[0] if docstring else None
                is_async = isinstance(node, ast.AsyncFunctionDef)
                symbols.append(
                    SymbolRecord(
                        name=node.name,
                        symbol_type=SymbolType.ASYNC_FUNCTION if is_async else SymbolType.FUNCTION,
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        decorators=decorators,
                        docstring=first_doc_line,
                    )
                )

            # 3. Classes
            elif isinstance(node, ast.ClassDef):
                decorators = [_format_expr(d) for d in node.decorator_list if _format_expr(d)]
                bases = [_format_expr(b) for b in node.bases if _format_expr(b)]
                docstring = ast.get_docstring(node)
                first_doc_line = docstring.strip().splitlines()[0] if docstring else None
                symbols.append(
                    SymbolRecord(
                        name=node.name,
                        symbol_type=SymbolType.CLASS,
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        decorators=decorators,
                        docstring=first_doc_line,
                        base_classes=bases,
                    )
                )

                # Extract methods inside class body
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_decorators = [_format_expr(d) for d in item.decorator_list if _format_expr(d)]
                        method_doc = ast.get_docstring(item)
                        first_method_doc = method_doc.strip().splitlines()[0] if method_doc else None
                        symbols.append(
                            SymbolRecord(
                                name=item.name,
                                symbol_type=SymbolType.METHOD,
                                line_number=item.lineno,
                                end_line_number=getattr(item, "end_lineno", item.lineno),
                                parent_symbol=node.name,
                                decorators=method_decorators,
                                docstring=first_method_doc,
                            )
                        )

            # 4. Entry point guard: if __name__ == "__main__":
            elif isinstance(node, ast.If):
                if _is_main_check(node):
                    has_main_block = True

            # 5. Exports: __all__ = [...]
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__all__"
                        and isinstance(node.value, (ast.List, ast.Tuple))
                    ):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exports.append(elt.value)

        return ModuleAnalysis(
            rel_path=rel_path,
            language="Python",
            symbols=symbols,
            imports=imports,
            exports=exports,
            has_main_block=has_main_block,
        )
