# analyzer.py
import os
from common import get_project_root

class ProjectAnalyzer:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or get_project_root()

    def analyze_modules(self) -> list[dict]:
        """Tự động phát hiện các module/cấu phần cốt lõi của dự án."""
        modules = []
        
        # 1. Quét Visualizer Extension
        visualizer_dir = os.path.join(self.root_dir, "extensions", "visualizer")
        if os.path.exists(visualizer_dir):
            modules.append({
                "name": "Visualizer Extension",
                "path": "extensions/visualizer",
                "purpose": "Sidebar dashboard that visualizes active work progress, stepper checkpoints, and token usage.",
                "details": "TypeScript VS Code Extension utilizing webview template."
            })
            
        # 2. Quét Workflow Runtime
        runtime_dir = os.path.join(self.root_dir, "skills", "workflow-runtime")
        if os.path.exists(runtime_dir):
            modules.append({
                "name": "Workflow Runtime",
                "path": "skills/workflow-runtime",
                "purpose": "Python-based CLI runtime engine that manages execution sessions and SQLite backed metrics.",
                "details": "Backed by SQLite database and manages .session.json updates."
            })
            
        # 3. Quét SDLC Skills
        skills_dir = os.path.join(self.root_dir, "skills")
        if os.path.exists(skills_dir):
            skills = []
            for item in os.listdir(skills_dir):
                full_path = os.path.join(skills_dir, item)
                if os.path.isdir(full_path) and item != "workflow-runtime" and not item.startswith("."):
                    skills.append(item)
            
            if skills:
                modules.append({
                    "name": "SDLC Skills Library",
                    "path": "skills",
                    "purpose": f"Collection of {len(skills)} modular software engineering skills (e.g. {', '.join(skills[:3])}).",
                    "details": f"Includes {len(skills)} independent prompt-driven or script-first modules."
                })
                
        return modules

    def get_database_info(self) -> list[dict]:
        databases = []
        # Check SQLite db file in .agents/
        db_path = os.path.join(self.root_dir, ".agents", "project_runtime.db")
        if os.path.exists(db_path):
            databases.append({
                "type": "SQLite",
                "path": ".agents/project_runtime.db",
                "purpose": "Persists active session usage, checkpoint status, and global metrics."
            })
            
        # Check Qdrant vector db config
        mem_config = os.path.join(self.root_dir, ".agents", "memory.config.json")
        if os.path.exists(mem_config):
            try:
                with open(mem_config, "r") as f:
                    import json
                    cfg = json.load(f)
                    if cfg.get("vector_provider") == "qdrant":
                        databases.append({
                            "type": "Qdrant Vector DB",
                            "path": "http://localhost:6333",
                            "purpose": "Vector similarity search and semantic retrieval for RAG memory search."
                        })
            except Exception:
                pass
                
        return databases
