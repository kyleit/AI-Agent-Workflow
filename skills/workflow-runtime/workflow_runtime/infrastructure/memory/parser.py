# parser.py
from __future__ import annotations

import os
import re
from typing import Any, cast


class CodeParser:
    @staticmethod
    def parse_python_file(content: str) -> dict[str, Any]:
        """Trích xuất danh sách import, class, và function từ tệp Python."""
        classes = re.findall(r"class\s+([a-zA-Z0-9_]+)(?:\s*\([^)]*\))?:", content)
        functions = re.findall(r"def\s+([a-zA-Z0-9_]+)\s*\(", content)
        raw_imports = re.findall(r"(?:import\s+([a-zA-Z0-9_, ]+)|from\s+([a-zA-Z0-9_.]+)\s+import)", content)

        flat_imports: list[str] = []
        for imp in raw_imports:
            imp_tuple = cast(tuple[str, str], imp)
            if imp_tuple[0]:
                for item in imp_tuple[0].split(","):
                    cleaned = item.strip()
                    if cleaned:
                        flat_imports.append(cleaned)
            if len(imp_tuple) > 1 and imp_tuple[1]:
                cleaned = imp_tuple[1].strip()
                if cleaned:
                    flat_imports.append(cleaned)

        return {
            "classes": classes,
            "functions": functions,
            "imports": sorted(list(set(flat_imports)))
        }

    @staticmethod
    def parse_typescript_file(content: str) -> dict[str, Any]:
        """Trích xuất classes, interfaces, functions, và imports từ tệp TS/JS."""
        classes = re.findall(r"class\s+([a-zA-Z0-9_]+)", content)
        interfaces = re.findall(r"interface\s+([a-zA-Z0-9_]+)", content)
        raw_functions = re.findall(r"(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*\([^)]*\)\s*=>)", content)

        flat_functions: list[str] = []
        for fn in raw_functions:
            fn_tuple = cast(tuple[str, str], fn)
            if fn_tuple[0]:
                flat_functions.append(fn_tuple[0])
            if len(fn_tuple) > 1 and fn_tuple[1]:
                flat_functions.append(fn_tuple[1])

        raw_imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", content)
        imports = [str(x) for x in raw_imports]

        return {
            "classes": classes,
            "interfaces": interfaces,
            "functions": flat_functions,
            "imports": sorted(list(set(imports)))
        }

    @classmethod
    def parse_file(cls, file_path: str) -> dict[str, Any]:
        _, ext = os.path.splitext(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return {"classes": [], "functions": [], "imports": []}

        if ext == ".py":
            return cls.parse_python_file(content)
        elif ext in [".ts", ".js", ".tsx", ".jsx"]:
            return cls.parse_typescript_file(content)
        return {"classes": [], "functions": [], "imports": []}


__all__ = ["CodeParser"]
