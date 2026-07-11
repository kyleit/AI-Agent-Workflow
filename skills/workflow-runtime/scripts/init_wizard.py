# init_wizard.py
import os
import sys
import json
import subprocess
from datetime import datetime

class RecommendationEngine:
    @staticmethod
    def get_recommendations(answers: dict) -> dict:
        recs = {}
        # Languages & frameworks recommendations
        primary_lang = answers.get("primary_language", "").lower()
        if primary_lang == "go":
            recs["backend_framework"] = "Fiber"
            recs["database"] = "PostgreSQL"
        elif primary_lang == "python":
            recs["backend_framework"] = "FastAPI"
            recs["database"] = "PostgreSQL"
        elif primary_lang == "typescript" or primary_lang == "javascript":
            recs["frontend_framework"] = "Svelte/SvelteKit"
            recs["database"] = "SQLite"
        else:
            recs["frontend_framework"] = "Svelte/SvelteKit"
            recs["database"] = "PostgreSQL"
        return recs

class ScaffoldPlanner:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)

    def generate_scaffold(self, config: dict) -> bool:
        try:
            os.makedirs(self.project_path, exist_ok=True)
            
            # 1. Create standard directories
            dirs = [
                ".agents",
                ".agents/state",
                ".agents/memory",
                ".agents/skills",
                ".agents/templates",
                ".agents/agents",
                ".agents/runtime",
                "docs",
                "docs/brainstorming",
                "docs/plans",
                "docs/designs",
                "docs/adr",
                "docs/issues",
                "docs/quick",
                "docs/debug",
                "docs/verification"
            ]
            for d in dirs:
                os.makedirs(os.path.join(self.project_path, d), exist_ok=True)

            # 2. Write project.config.json
            config_path = os.path.join(self.project_path, ".agents", "project.config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            # 3. Write PROJECT_PROFILE.md
            profile_path = os.path.join(self.project_path, ".agents", "PROJECT_PROFILE.md")
            profile_content = f"""# Project Profile: {config.get('project', {}).get('name', 'My Project')}

## 1. Project Information
- **Display Name**: {config.get('project', {}).get('display_name', 'My Project')}
- **Description**: {config.get('project', {}).get('description', 'A project initialized with AIWF')}
- **Ecosystem**: {', '.join(config.get('languages', []))}
- **Target Topology**: {config.get('topology', {}).get('type', 'single-module')}

## 2. Architecture & Decisions
- **Selected Pattern**: {config.get('architecture', {}).get('pattern', 'DDD + Clean Architecture')}
- **Database**: {config.get('database', {}).get('engine', 'SQLite')}
"""
            with open(profile_path, "w", encoding="utf-8") as f:
                f.write(profile_content)

            # 4. Initialize Git if selected
            git_opt = config.get("git", {})
            if git_opt.get("initialize", True):
                git_path = os.path.join(self.project_path, ".git")
                if not os.path.exists(git_path):
                    branch = git_opt.get("default_branch", "main")
                    subprocess.run(["git", "init", "-b", branch], cwd=self.project_path, capture_output=True)
                    
                    # Write basic .gitignore
                    gitignore_path = os.path.join(self.project_path, ".gitignore")
                    if not os.path.exists(gitignore_path):
                        with open(gitignore_path, "w", encoding="utf-8") as gf:
                            gf.write(".agents/runtime/\n.agents/state/choice-response.json\n*.tmp\n")

            return True
        except Exception as e:
            print(f"Scaffolding failed: {e}", file=sys.stderr)
            return False

class InitQuestionnaire:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.draft_dir = os.path.join(self.project_path, ".aiwf-init")
        self.draft_file = os.path.join(self.draft_dir, "state.json")

    def save_draft(self, state: dict):
        os.makedirs(self.draft_dir, exist_ok=True)
        with open(self.draft_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_draft(self) -> dict:
        if os.path.exists(self.draft_file):
            try:
                with open(self.draft_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def cleanup_draft(self):
        if os.path.exists(self.draft_file):
            try:
                os.remove(self.draft_file)
                os.rmdir(self.draft_dir)
            except Exception:
                pass

    def run_interactive(self, resume: bool = False) -> dict:
        state = {}
        if resume:
            state = self.load_draft()
            print(f"Resuming from previous draft... Loaded {len(state)} answers.")

        # Interactive Wizard helper
        def ask_question(key: str, prompt: str, default: str) -> str:
            if key in state:
                return state[key]
            print(f"{prompt} [{default}]: ", end="")
            sys.stdout.flush()
            val = sys.stdin.readline().strip()
            if not val:
                val = default
            state[key] = val
            self.save_draft(state)
            return val

        # Questions
        name = ask_question("name", "Enter project name", "my-aiwf-project")
        display_name = ask_question("display_name", "Enter display name", name.title())
        desc = ask_question("description", "Enter description", "A new AIWF project")
        lang = ask_question("primary_language", "Enter primary language (Go/Python/TypeScript)", "Python")
        
        # Recommendations
        recs = RecommendationEngine.get_recommendations(state)
        default_db = recs.get("database", "PostgreSQL")
        db = ask_question("database", "Enter database engine", default_db)

        git_init = ask_question("git_init", "Initialize Git repository? (y/n)", "y").lower() in ["y", "yes"]

        # Build final config structure
        config = {
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
            },
            "created_at": datetime.now().astimezone().isoformat(),
            "updated_at": datetime.now().astimezone().isoformat()
        }

        self.cleanup_draft()
        return config

def handle_init(args) -> int:
    path = args.path or "."
    wizard = InitQuestionnaire(path)
    planner = ScaffoldPlanner(path)

    if args.non_interactive:
        config_path = args.config
        if not config_path or not os.path.exists(config_path):
            print("Error: --config file is required in --non-interactive mode.", file=sys.stderr)
            return 1
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            return 1
    else:
        config = wizard.run_interactive(args.resume)

    if args.dry_run:
        print("[DRY-RUN] Planned files to initialize:")
        print(f"- {os.path.join(path, '.agents/project.config.json')}")
        print(f"- {os.path.join(path, '.agents/PROJECT_PROFILE.md')}")
        return 0

    print("Initializing workspace files...")
    if planner.generate_scaffold(config):
        print(f"Project initialized successfully at {os.path.abspath(path)}.")
        return 0
    else:
        print("Initialization failed.", file=sys.stderr)
        return 1
