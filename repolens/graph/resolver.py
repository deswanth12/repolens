"""Module and import resolution engine.

Resolves Python import statements to concrete repository files
or classifies them as external/standard-library dependencies.
"""

from __future__ import annotations

import posixpath
from pathlib import Path

from repolens.models import ImportRecord


class ImportResolver:
    """Resolves import records against the repository's known file list."""

    def __init__(self, known_source_paths: set[str]) -> None:
        # Normalized POSIX paths of all source files in repo
        self.known_paths = {p.replace("\\", "/") for p in known_source_paths}
        self._build_index()

    def _build_index(self) -> None:
        """Builds lookup dictionaries for fast resolution."""
        self.stem_to_path: dict[str, str] = {}
        self.init_to_path: dict[str, str] = {}

        for p in self.known_paths:
            path_obj = Path(p)
            # Exact path
            self.stem_to_path[p] = p
            # Stem without extension (e.g., "repolens/models" -> "repolens/models.py")
            stem_key = p.rsplit(".", 1)[0]
            self.stem_to_path[stem_key] = p

            # Package directory index: __init__.py, index.js, index.ts, index.jsx, index.tsx
            if path_obj.name in {"__init__.py", "index.js", "index.ts", "index.jsx", "index.tsx"}:
                parent_dir = path_obj.parent.as_posix()
                if parent_dir != ".":
                    self.init_to_path[parent_dir] = p

    def resolve(self, source_rel_path: str, imp: ImportRecord) -> tuple[str, bool]:
        """Resolves an import to a repository file or external dependency.

        Returns (target, is_internal).
        """
        source_rel_path = source_rel_path.replace("\\", "/")
        source_dir = Path(source_rel_path).parent.as_posix()
        if source_dir == ".":
            source_dir = ""

        # 1. Check JS/TS path aliases like '@/components/Button' or '~/utils'
        if imp.module and (imp.module.startswith("@/") or imp.module.startswith("~/")):
            alias_path = imp.module[2:]
            for prefix in ["src/", ""]:
                cand = posixpath.normpath(f"{prefix}{alias_path}").lstrip("/")
                if cand in self.stem_to_path:
                    return self.stem_to_path[cand], True
                if cand in self.init_to_path:
                    return self.init_to_path[cand], True
                for ext in [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".mjs", ".cjs"]:
                    if f"{cand}{ext}" in self.stem_to_path:
                        return self.stem_to_path[f"{cand}{ext}"], True
            return imp.module, True

        # 2. JS/TS explicit relative imports (starts with ./ or ../)
        if imp.module and (imp.module.startswith("./") or imp.module.startswith("../")):
            target = self._resolve_relative_path(source_dir, imp.module)
            if target:
                return target, True
            norm_cand = posixpath.normpath(posixpath.join(source_dir, imp.module))
            return norm_cand, True

        # 3. Python relative imports (level > 0, from . or from ..)
        if imp.level > 0:
            target = self._resolve_python_relative(source_dir, imp)
            if target:
                return target, True
            return imp.module or "relative_unresolved", True

        # 4. Absolute imports: import os, from repolens.models import FileRecord
        module_path = imp.module.replace(".", "/")

        # 4a. Check if module directly matches a known file
        if module_path in self.stem_to_path:
            return self.stem_to_path[module_path], True

        # 4b. Check if module matches a package directory with __init__.py / index file
        if module_path in self.init_to_path:
            return self.init_to_path[module_path], True

        # 4c. Check under "src/" if repository uses src layout
        src_module = f"src/{module_path}"
        if src_module in self.stem_to_path:
            return self.stem_to_path[src_module], True
        if src_module in self.init_to_path:
            return self.init_to_path[src_module], True

        # 4d. For "from x import y", check if y is actually a file module under x
        for name in imp.imported_names:
            submodule_path = f"{module_path}/{name}"
            if submodule_path in self.stem_to_path:
                return self.stem_to_path[submodule_path], True
            src_submodule = f"src/{submodule_path}"
            if src_submodule in self.stem_to_path:
                return self.stem_to_path[src_submodule], True

        # Not found in repository files -> External dependency
        top_pkg = imp.module.split(".")[0] if imp.module else "unknown"
        return top_pkg, False

    def _resolve_relative_path(self, source_dir: str, rel_path: str) -> str | None:
        """Resolves file-system relative path (e.g. ./utils or ../components/Button)."""
        candidate = posixpath.normpath(posixpath.join(source_dir, rel_path))
        if candidate.startswith("./"):
            candidate = candidate[2:]

        if candidate in self.stem_to_path:
            return self.stem_to_path[candidate]
        if candidate in self.init_to_path:
            return self.init_to_path[candidate]

        for ext in [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".mjs", ".cjs"]:
            cand_ext = f"{candidate}{ext}"
            if cand_ext in self.stem_to_path:
                return self.stem_to_path[cand_ext]

        return None

    def _resolve_python_relative(self, source_dir: str, imp: ImportRecord) -> str | None:
        """Resolves Python-style relative import against source file's directory."""
        dir_parts = source_dir.split("/") if source_dir else []
        steps_up = imp.level - 1

        if steps_up > len(dir_parts):
            return None

        base_parts = dir_parts[: len(dir_parts) - steps_up] if steps_up > 0 else dir_parts
        base_dir = "/".join(base_parts)

        sub_path = imp.module.replace(".", "/") if imp.module else ""
        candidate = f"{base_dir}/{sub_path}".strip("/") if base_dir else sub_path

        if candidate in self.stem_to_path:
            return self.stem_to_path[candidate]
        if candidate in self.init_to_path:
            return self.init_to_path[candidate]

        # Check imported names as submodules
        for name in imp.imported_names:
            sub_candidate = f"{candidate}/{name}".strip("/")
            if sub_candidate in self.stem_to_path:
                return self.stem_to_path[sub_candidate]
            if sub_candidate in self.init_to_path:
                return self.init_to_path[sub_candidate]

        return None
