# parser.py
import re
import os
from common import get_project_root

class CodeParser:
    @staticmethod
    def parse_python_file(content: str) -> dict:
        """Trích xuất danh sách import, class, và function từ tệp Python."""
        classes = re.findall(r"class\s+([a-zA-Z0-9_]+)(?:\s*\([^)]*\))?:", content)
        functions = re.findall(r"def\s+([a-zA-Z0-9_]+)\s*\(", content)
        imports = re.findall(r"(?:import\s+([a-zA-Z0-9_, ]+)|from\s+([a-zA-Z0-9_.]+)\s+import)", content)
        
        flat_imports = []
        for imp in imports:
            if imp[0]:
                flat_imports.extend([i.strip() for i in imp[0].split(",")])
            if imp[1]:
                flat_imports.append(imp[1].strip())
                
        return {
            "classes": classes,
            "functions": functions,
            "imports": list(set(flat_imports))
        }

    @staticmethod
    def parse_typescript_file(content: str) -> dict:
        """Trích xuất classes, interfaces, functions, và imports từ tệp TS/JS."""
        classes = re.findall(r"class\s+([a-zA-Z0-9_]+)", content)
        interfaces = re.findall(r"interface\s+([a-zA-Z0-9_]+)", content)
        functions = re.findall(r"(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*\([^)]*\)\s*=>)", content)
        
        flat_functions = []
        for fn in functions:
            if fn[0]:
                flat_functions.append(fn[0])
            if fn[1]:
                flat_functions.append(fn[1])
                
        imports = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", content)
        
        return {
            "classes": classes,
            "interfaces": interfaces,
            "functions": flat_functions,
            "imports": list(set(imports))
        }

    @classmethod
    def parse_file(cls, file_path: str) -> dict:
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
        else:
            return {"classes": [], "functions": [], "imports": []}
