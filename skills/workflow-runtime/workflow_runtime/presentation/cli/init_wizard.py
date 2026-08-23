from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from typing import Any, cast


class RecommendationEngine:
    @staticmethod
    def get_recommendations(answers: dict[str, Any]) -> dict[str, Any]:
        recs: dict[str, Any] = {}
        primary_lang = str(answers.get("primary_language", "")).lower()
        if primary_lang == "go":
            recs["backend_framework"] = "Fiber"
            recs["database"] = "PostgreSQL"
        elif primary_lang == "python":
            recs["backend_framework"] = "FastAPI"
            recs["database"] = "PostgreSQL"
        elif primary_lang in ("typescript", "javascript"):
            recs["frontend_framework"] = "Svelte/SvelteKit"
            recs["database"] = "SQLite"
        else:
            recs["frontend_framework"] = "Svelte/SvelteKit"
            recs["database"] = "PostgreSQL"
        return recs


class ScaffoldPlanner:
    def __init__(self, project_path: str) -> None:
        self.project_path = os.path.abspath(project_path)

    def generate_scaffold(self, config: dict[str, Any]) -> bool:
        try:
            os.makedirs(self.project_path, exist_ok=True)

            dirs = [
                ".agents",
                ".agents/state",
                ".agents/memory",
                ".agents/skills",
                ".agents/templates",
                ".agents/agents",
                ".agents/runtime",
                "docs"
            ]
            for d in dirs:
                os.makedirs(os.path.join(self.project_path, d), exist_ok=True)

            config_path = os.path.join(self.project_path, ".agents", "project.config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            raw_proj = config.get("project")
            proj_dict = cast(dict[str, Any], raw_proj) if isinstance(raw_proj, dict) else {}

            raw_langs = config.get("languages")
            langs_list = cast(list[Any], raw_langs) if isinstance(raw_langs, list) else []
            langs_str = ", ".join(str(x) for x in langs_list)

            raw_topo = config.get("topology")
            topo_dict = cast(dict[str, Any], raw_topo) if isinstance(raw_topo, dict) else {}

            raw_arch = config.get("architecture")
            arch_dict = cast(dict[str, Any], raw_arch) if isinstance(raw_arch, dict) else {}

            raw_db = config.get("database")
            db_dict = cast(dict[str, Any], raw_db) if isinstance(raw_db, dict) else {}

            profile_path = os.path.join(self.project_path, ".agents", "PROJECT_PROFILE.md")
            profile_content = f"""# Project Profile: {proj_dict.get('name', 'My Project')}

## 1. Project Information
- **Display Name**: {proj_dict.get('display_name', 'My Project')}
- **Description**: {proj_dict.get('description', 'A project initialized with AIWF')}
- **Ecosystem**: {langs_str}
- **Target Topology**: {topo_dict.get('type', 'single-module')}

## 2. Architecture & Decisions
- **Selected Pattern**: {arch_dict.get('pattern', 'DDD + Clean Architecture')}
- **Database**: {db_dict.get('engine', 'SQLite')}
"""
            with open(profile_path, "w", encoding="utf-8") as f:
                f.write(profile_content)

            current_file = os.path.abspath(__file__)
            skill_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
            fw_root = os.path.dirname(os.path.dirname(skill_root))

            if not os.path.exists(os.path.join(fw_root, "MANIFEST.json")):
                fw_root = os.environ.get("AIWF_HOME", fw_root)

            if os.path.exists(os.path.join(fw_root, "MANIFEST.json")):
                print(f"Copying framework assets from {fw_root}...")

                for d in ["skills", "templates", "agents", "runtime"]:
                    src_dir = os.path.join(fw_root, d)
                    dst_dir = os.path.join(self.project_path, ".agents", d)
                    if os.path.exists(src_dir):
                        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

                for f_name in ["AI_RULES.md", "AGENTS.md", "SKILLS.md"]:
                    src_file = os.path.join(fw_root, f_name)
                    dst_file = os.path.join(self.project_path, ".agents", f_name)
                    if os.path.exists(src_file):
                        shutil.copy2(src_file, dst_file)
            else:
                print(f"Warning: Framework root with MANIFEST.json not found at {fw_root}. Skills were not copied.", file=sys.stderr)

            raw_git = config.get("git")
            git_opt = cast(dict[str, Any], raw_git) if isinstance(raw_git, dict) else {}
            if git_opt.get("initialize", True):
                git_path = os.path.join(self.project_path, ".git")
                if not os.path.exists(git_path):
                    branch = str(git_opt.get("default_branch", "main"))
                    subprocess.run(["git", "init", "-b", branch], cwd=self.project_path, capture_output=True)

                    gitignore_path = os.path.join(self.project_path, ".gitignore")
                    if not os.path.exists(gitignore_path):
                        with open(gitignore_path, "w", encoding="utf-8") as gf:
                            gf.write(".agents/runtime/\n.agents/state/choice-response.json\n*.tmp\n")

            return True
        except Exception as e:
            print(f"Scaffolding failed: {e}", file=sys.stderr)
            return False


class InitQuestionnaire:
    def __init__(self, project_path: str) -> None:
        self.project_path = os.path.abspath(project_path)
        self.draft_dir = os.path.join(self.project_path, ".aiwf-init")
        self.draft_file = os.path.join(self.draft_dir, "state.json")

    def save_draft(self, state: dict[str, Any]) -> None:
        os.makedirs(self.draft_dir, exist_ok=True)
        with open(self.draft_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_draft(self) -> dict[str, Any]:
        if os.path.exists(self.draft_file):
            try:
                with open(self.draft_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    return cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
            except Exception:
                pass
        return {}

    def cleanup_draft(self) -> None:
        if os.path.exists(self.draft_file):
            try:
                os.remove(self.draft_file)
                os.rmdir(self.draft_dir)
            except Exception:
                pass

    def run_interactive(self, resume: bool = False) -> dict[str, Any]:
        state: dict[str, Any] = {}
        if resume:
            state = self.load_draft()
            print(f"Resuming from previous draft... Loaded {len(state)} answers.")

        def ask_question(key: str, prompt: str, default: str) -> str:
            if key in state:
                return str(state[key])
            print(f"{prompt} [{default}]: ", end="")
            sys.stdout.flush()
            val = sys.stdin.readline().strip()
            if not val:
                val = default
            state[key] = val
            self.save_draft(state)
            return val

        name = ask_question("name", "Enter project name", "my-aiwf-project")
        display_name = ask_question("display_name", "Enter display name", name.title())
        desc = ask_question("description", "Enter description", "A new AIWF project")
        lang = ask_question("primary_language", "Enter primary language (Go/Python/TypeScript)", "Python")

        recs = RecommendationEngine.get_recommendations(state)
        default_db = str(recs.get("database", "PostgreSQL"))
        db = ask_question("database", "Enter database engine", default_db)

        git_init = ask_question("git_init", "Initialize Git repository? (y/n)", "y").lower() in ["y", "yes"]

        config: dict[str, Any] = {
            "schema_version": "1.0.0",
            "project": {
                "name": name,
                "display_name": display_name,
                "description": desc,
                "version": "1.0.0"
            },
            "topology": {
                "type": "single-module"
            },
            "architecture": {
                "pattern": "DDD + Clean Architecture"
            },
            "languages": [lang],
            "database": {
                "engine": db
            },
            "git": {
                "initialize": git_init,
                "default_branch": "main"
            }
        }

        self.cleanup_draft()
        return config


__all__ = ["RecommendationEngine", "ScaffoldPlanner", "InitQuestionnaire"]
