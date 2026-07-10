# scanner.py
import os
from collections import Counter
from common import get_project_root
from filesystem import get_project_files

LANG_EXT_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".html": "HTML",
    ".css": "CSS"
}

class ProjectScanner:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or get_project_root()
        self._files = None

    @property
    def files(self) -> list[str]:
        if self._files is None:
            self._files = get_project_files(self.root_dir)
        return self._files

    def detect_languages(self) -> list[str]:
        exts = []
        for file in self.files:
            _, ext = os.path.splitext(file)
            if ext in LANG_EXT_MAP:
                exts.append(LANG_EXT_MAP[ext])
        
        if not exts:
            return ["Unknown"]
            
        counter = Counter(exts)
        # Sắp xếp ngôn ngữ giảm dần theo tần suất xuất hiện
        sorted_langs = [item[0] for item in counter.most_common()]
        return sorted_langs

    def detect_frameworks(self, languages: list[str]) -> list[str]:
        frameworks = []
        
        # Check Node.js/TypeScript frameworks
        package_json_path = os.path.join(self.root_dir, "package.json")
        if os.path.exists(package_json_path):
            frameworks.append("Node.js")
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    import json
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "vscode" in deps or "@types/vscode" in deps or "vscode-test" in deps:
                        frameworks.append("VS Code Extension API")
                    if "react" in deps:
                        frameworks.append("React")
                    if "vue" in deps:
                        frameworks.append("Vue")
            except Exception:
                pass
                
        # Check Go frameworks
        go_mod_path = os.path.join(self.root_dir, "go.mod")
        if os.path.exists(go_mod_path):
            frameworks.append("Go Modules")
            
        # Check Python frameworks
        pyproject_toml = os.path.join(self.root_dir, "pyproject.toml")
        requirements_txt = os.path.join(self.root_dir, "requirements.txt")
        if os.path.exists(pyproject_toml) or os.path.exists(requirements_txt):
            frameworks.append("Python Pip/Poetry")
            
        return frameworks

    def detect_build_commands(self) -> list[dict]:
        commands = []
        makefile_path = os.path.join(self.root_dir, "Makefile")
        if os.path.exists(makefile_path):
            commands.append({"name": "Makefile Build", "command": "make"})
            
        package_json_path = os.path.join(self.root_dir, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    import json
                    pkg = json.load(f)
                    scripts = pkg.get("scripts", {})
                    for name in ["compile", "build", "package", "test"]:
                        if name in scripts:
                            commands.append({"name": f"npm run {name}", "command": f"npm run {name}"})
            except Exception:
                pass
                
        return commands
