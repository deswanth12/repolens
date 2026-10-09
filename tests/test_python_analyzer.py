"""Tests for the Python AST analyzer."""

from pathlib import Path

from repolens.analyzers.python_analyzer import PythonAnalyzer
from repolens.models import FileCategory, FileRecord, SymbolType


def test_python_analyzer_can_analyze():
    analyzer = PythonAnalyzer()
    py_record = FileRecord("src/app.py", ".py", "Python", FileCategory.SOURCE, 100)
    test_record = FileRecord("tests/test_app.py", ".py", "Python", FileCategory.TEST, 100)
    doc_record = FileRecord("README.md", ".md", "Markdown", FileCategory.DOCUMENTATION, 100)
    bin_record = FileRecord("data.py", ".py", "Python", FileCategory.SOURCE, 100, is_binary=True)

    assert analyzer.can_analyze(py_record) is True
    assert analyzer.can_analyze(test_record) is True
    assert analyzer.can_analyze(doc_record) is False
    assert analyzer.can_analyze(bin_record) is False


def test_python_analyzer_symbols_and_imports(tmp_path: Path):
    source = '''"""Module docstring."""
import os
import sys as system
from pathlib import Path, PurePath
from . import local_mod
from ..parent import ParentClass

__all__ = ["MyClass", "run_job"]

@decorator_a
class MyClass(ParentClass):
    """Class docstring."""
    
    @staticmethod
    def method_one(self):
        pass

    async def async_method(self):
        pass

def run_job():
    """Run function."""
    pass

async def async_task():
    pass

if __name__ == "__main__":
    run_job()
'''
    file_path = tmp_path / "sample.py"
    file_path.write_text(source, encoding="utf-8")

    analyzer = PythonAnalyzer()
    analysis = analyzer.analyze(file_path, "sample.py")

    assert analysis.rel_path == "sample.py"
    assert analysis.language == "Python"
    assert analysis.parse_error is None
    assert analysis.has_main_block is True
    assert analysis.exports == ["MyClass", "run_job"]

    # Verify imports
    import_mods = [i.module for i in analysis.imports]
    assert "os" in import_mods
    assert "sys" in import_mods
    assert "pathlib" in import_mods
    assert "" in import_mods  # from . import local_mod (module is empty, level is 1)
    assert "parent" in import_mods

    # Check imported names
    pathlib_import = next(i for i in analysis.imports if i.module == "pathlib")
    assert "Path" in pathlib_import.imported_names
    assert "PurePath" in pathlib_import.imported_names

    # Verify symbols
    symbols_by_name = {s.name: s for s in analysis.symbols}
    assert "MyClass" in symbols_by_name
    assert symbols_by_name["MyClass"].symbol_type == SymbolType.CLASS
    assert symbols_by_name["MyClass"].base_classes == ["ParentClass"]
    assert "method_one" in symbols_by_name
    assert symbols_by_name["method_one"].parent_symbol == "MyClass"
    assert symbols_by_name["method_one"].symbol_type == SymbolType.METHOD

    assert "async_method" in symbols_by_name
    assert symbols_by_name["async_method"].parent_symbol == "MyClass"

    assert "run_job" in symbols_by_name
    assert symbols_by_name["run_job"].symbol_type == SymbolType.FUNCTION

    assert "async_task" in symbols_by_name
    assert symbols_by_name["async_task"].symbol_type == SymbolType.ASYNC_FUNCTION


def test_python_analyzer_syntax_error(tmp_path: Path):
    bad_code = "def broken(:\n    pass\n"
    file_path = tmp_path / "broken.py"
    file_path.write_text(bad_code, encoding="utf-8")

    analyzer = PythonAnalyzer()
    analysis = analyzer.analyze(file_path, "broken.py")

    assert analysis.parse_error is not None
    assert "Syntax error" in analysis.parse_error
    assert len(analysis.symbols) == 0


def test_python_analyzer_conditional_and_nested_imports(tmp_path: Path):
    code = """
try:
    import tomllib
except ImportError:
    import tomli as tomllib

if True:
    from typing import Optional, List

def inner():
    import math

if __name__ == '__main__':
    print('running')
"""
    file_path = tmp_path / "conditional.py"
    file_path.write_text(code, encoding="utf-8")

    analyzer = PythonAnalyzer()
    analysis = analyzer.analyze(file_path, "conditional.py")

    assert analysis.parse_error is None
    assert analysis.has_main_block is True
    modules = {imp.module for imp in analysis.imports}
    assert "tomllib" in modules
    assert "tomli" in modules
    assert "typing" in modules
    assert "math" in modules
