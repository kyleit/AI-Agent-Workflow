import os
import json
from datetime import datetime

class SessionBootstrapGuard:
    workspace_root: str
    session_id: str
    session_dir: str
    session_path: str

    def __init__(self, workspace_root: str, session_id: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self.session_id = session_id
        self.session_dir = os.path.join(self.workspace_root, ".agents", "state", "sessions")
        self.session_path = os.path.join(self.session_dir, f"{session_id}.json")

    def is_initialized(self) -> bool:
        if not os.path.exists(self.session_path):
            return False
        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("initialized") is True
        except Exception:
            return False

    def initialize_workspace(self) -> tuple[bool, str]:
        try:
            # 1. Ensure state dirs exist
            os.makedirs(self.session_dir, exist_ok=True)
            os.makedirs(os.path.join(self.workspace_root, ".agents", "config"), exist_ok=True)
            os.makedirs(os.path.join(self.workspace_root, ".agents", "skills"), exist_ok=True)
            os.makedirs(os.path.join(self.workspace_root, ".agents", "state"), exist_ok=True)

            # 2. project.config.json
            p_config_path = os.path.join(self.workspace_root, ".agents", "project.config.json")
            if not os.path.exists(p_config_path):
                p_config = {
                    "project_id": "ai-skill-framework",
                    "workspace_id": "workspace-id",
                    "permission_mode": "sandbox",
                    "created_at": datetime.now().astimezone().isoformat(),
                    "updated_at": datetime.now().astimezone().isoformat()
                }
                with open(p_config_path, "w", encoding="utf-8") as f:
                    json.dump(p_config, f, indent=2)

            # 3. permissions.json
            perm_path = os.path.join(self.workspace_root, ".agents", "config", "permissions.json")
            if not os.path.exists(perm_path):
                perm_config = {
                    "mode": "sandbox"
                }
                with open(perm_path, "w", encoding="utf-8") as f:
                    json.dump(perm_config, f, indent=2)

            # 4. registry.json
            reg_path = os.path.join(self.workspace_root, ".agents", "skills", "registry.json")
            if not os.path.exists(reg_path):
                reg_config = {
                    "brainstorming": {
                        "name": "brainstorming",
                        "phase": "discovery",
                        "inputs": ["feature_request", "project_context"],
                        "required_outputs": ["docs/brainstorming/*.md"],
                        "next_phase": "planning"
                    },
                    "brainstorming-to-plan": {
                        "name": "brainstorming-to-plan",
                        "phase": "planning",
                        "inputs": ["brainstorm_file"],
                        "required_outputs": ["docs/planning/*_plan.md"],
                        "next_phase": "Gate1_PlanApproval"
                    },
                    "blueprint": {
                        "name": "blueprint-to-implementation",
                        "phase": "blueprint",
                        "inputs": ["plan_file"],
                        "required_outputs": ["docs/blueprints/*_blueprint.md"],
                        "next_phase": "Gate2_BlueprintApproval"
                    }
                }
                with open(reg_path, "w", encoding="utf-8") as f:
                    json.dump(reg_config, f, indent=2)

            # 5. Write session initialized file
            session_state = {
                "session_id": self.session_id,
                "initialized": True,
                "initialized_at": datetime.now().astimezone().isoformat(),
                "workspace_ready": True,
                "runtime_ready": True
            }
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump(session_state, f, indent=2)

            return True, ""
        except Exception as e:
            return False, str(e)

    def reset_session(self) -> None:
        if os.path.exists(self.session_path):
            try:
                os.remove(self.session_path)
            except Exception:
                pass
