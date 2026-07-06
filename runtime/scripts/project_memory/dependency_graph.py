# dependency_graph.py
import os
from parser import CodeParser
from common import get_project_root

class DependencyGraph:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or get_project_root()
        self.graph = {}

    def build_graph(self, files: list[str]) -> dict:
        """Xây dựng quan hệ import chéo giữa các tệp tin trong dự án."""
        for file in files:
            full_path = os.path.join(self.root_dir, file)
            if not os.path.exists(full_path):
                continue
                
            parsed = CodeParser.parse_file(full_path)
            imports = parsed.get("imports", [])
            
            resolved_imports = []
            for imp in imports:
                # Giải quyết đường dẫn import tương đối cơ bản
                if imp.startswith("."):
                    # Resolve relative to file directory
                    dir_path = os.path.dirname(file)
                    resolved = os.path.normpath(os.path.join(dir_path, imp))
                    resolved_imports.append(resolved.replace("\\", "/"))
                else:
                    resolved_imports.append(imp)
                    
            self.graph[file] = resolved_imports
        return self.graph
