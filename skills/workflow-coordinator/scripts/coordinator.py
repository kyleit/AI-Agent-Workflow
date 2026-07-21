# coordinator.py
import sys
import os
import json
import argparse
import re
from typing import Any

# Resolve sys.path to find workflow-runtime sibling scripts from either:
# - skills/workflow-coordinator/scripts
# - .agents/skills/workflow-coordinator/scripts
_here = os.path.abspath(os.path.dirname(__file__))
for _candidate in [
    os.path.abspath(os.path.join(_here, "..", "..", "workflow-runtime", "scripts")),
    os.path.abspath(os.path.join(_here, "..", "..", "..", "..", "skills", "workflow-runtime", "scripts")),
]:
    if os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.append(_candidate)

from state_store import get_state_store, get_active_work_item_id, set_active_work_item_id  # type: ignore
from session import load_session, save_session_atomic  # type: ignore

class GateViolationError(Exception):
    pass

class NoDaemonViolationError(Exception):
    pass

class ParallelGateViolationError(Exception):
    pass

class WorkflowCoordinator:
    workspace_root: str

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def run_tick(self, prompt: str, work_item_id: str | None = None) -> dict[str, Any]:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
            
        if work_item_id:
            set_active_work_item_id(work_item_id)
        else:
            work_item_id = get_active_work_item_id() or "WF-GLOBAL"
            
        # Load states
        store = get_state_store()
        workflow = store.get("workflow") or {}
        approvals = store.get("approvals") or {}
        
        # Check active workflow resume priority (Task 1.1)
        should_resume, active_skill, active_command = self._check_resume_priority()
        
        logs = []
        if should_resume and prompt.strip().lower() == "continue":
            logs.append(f"> Resuming active workflow stage. Next skill: {active_skill}")
            
            # Write state updates
            workflow["active_workflow"] = "standard-development"
            workflow["suggested_next_skill"] = active_skill
            workflow["suggested_next_command"] = active_command
            store.set("workflow", workflow)
            
            return {
                "status": "success",
                "active_workflow": "standard-development",
                "active_phase": workflow.get("active_phase"),
                "checkpoint": workflow.get("checkpoint", 1),
                "suggested_next_skill": active_skill,
                "suggested_next_command": active_command,
                "suggested_next_skill_metadata": {
                    "skill": active_skill,
                    "command": active_command,
                    "reason": "Resuming active workflow.",
                    "expected_input": workflow.get("resume_state", {}).get("expected_input", "")
                },
                "logs": logs
            }
            
        # Classify intent (Task 1.2)
        intent_info = self._classify_intent(prompt)
        target_skill = intent_info["skill"]
        target_command = intent_info["command"]
        target_phase = intent_info["phase"]
        
        # Verify safety gates (Task 1.4)
        try:
            self._verify_safety_gates(target_skill, target_phase)
        except GateViolationError as e:
            return {
                "status": "waiting_for_approval",
                "active_workflow": None,
                "active_phase": None,
                "checkpoint": workflow.get("checkpoint", 1),
                "suggested_next_skill": target_skill,
                "suggested_next_command": target_command,
                "suggested_next_skill_metadata": {
                    "skill": target_skill,
                    "command": target_command,
                    "reason": str(e),
                    "expected_input": ""
                },
                "logs": [f"> Safety gate violation: {e}"]
            }
            
        # Verify blueprint gate (Task 1.5)
        if target_skill == "blueprint-to-implementation":
            if not self._verify_blueprint_gate(work_item_id):
                return {
                    "status": "waiting_for_approval",
                    "active_workflow": None,
                    "active_phase": None,
                    "checkpoint": workflow.get("checkpoint", 1),
                    "suggested_next_skill": target_skill,
                    "suggested_next_command": target_command,
                    "suggested_next_skill_metadata": {
                        "skill": target_skill,
                        "command": target_command,
                        "reason": f"Blueprint not approved for work item {work_item_id}.",
                        "expected_input": ""
                    },
                    "logs": [f"> Blueprint gate check failed for {work_item_id}."]
                }
                
        # Prevent parallel mode auto selection (Task 1.8)
        if "parallel" in prompt.lower() and "sequential" not in prompt.lower():
            raise ParallelGateViolationError("Parallel mode execution must be manually selected by user.")

        # Write updates
        workflow["active_workflow"] = "standard-development"
        workflow["active_phase"] = target_phase
        workflow["suggested_next_skill"] = target_skill
        workflow["suggested_next_command"] = target_command
        store.set("workflow", workflow)
        
        logs.append(f"> Intent classified: {intent_info['intent']}. Suggestions prepared.")
        
        return {
            "status": "success",
            "active_workflow": "standard-development",
            "active_phase": target_phase,
            "checkpoint": workflow.get("checkpoint", 1),
            "suggested_next_skill": target_skill,
            "suggested_next_command": target_command,
            "suggested_next_skill_metadata": {
                "skill": target_skill,
                "command": target_command,
                "reason": f"Intent match: {intent_info['intent']}.",
                "expected_input": ""
            },
            "logs": logs
        }

    def _check_resume_priority(self) -> tuple[bool, str, str]:
        store = get_state_store()
        workflow = store.get("workflow") or {}
        active_wf = workflow.get("active_workflow")
        suggested = workflow.get("suggested_next_skill")
        cmd = workflow.get("suggested_next_command", "run")
        if active_wf and suggested:
            return True, suggested, cmd
        return False, "", ""

    def _classify_intent(self, prompt: str) -> dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Heuristic checks
        if any(kw in prompt_lower for kw in ["fix", "bug", "error", "issue", "typo"]):
            return {
                "intent": "bug_fix",
                "skill": "quick-fix",
                "command": "fix",
                "phase": "debug"
            }
        elif any(kw in prompt_lower for kw in ["feature", "add", "new", "create"]):
            return {
                "intent": "feature_request",
                "skill": "quick-feature",
                "command": "feature",
                "phase": "implementation"
            }
        elif "blueprint" in prompt_lower:
            return {
                "intent": "blueprint",
                "skill": "blueprint-to-implementation",
                "command": "implement",
                "phase": "implementation"
            }
            
        # Default fallback (suggest brainstorming)
        return {
            "intent": "chat",
            "skill": "brainstorming",
            "command": "brainstorm",
            "phase": "brainstorming"
        }

    def _verify_safety_gates(self, target_skill: str, target_phase: str) -> bool:
        store = get_state_store()
        approvals = store.get("approvals") or {}
        
        if target_phase in ["implementation", "debug"] and target_skill in ["blueprint-to-implementation", "quick-feature", "quick-fix"]:
            bp = approvals.get("blueprint", {})
            work_item_id = get_active_work_item_id() or ""
            ok, reason = self._validate_blueprint_approval(bp, work_item_id)
            if not ok and target_skill == "blueprint-to-implementation":
                raise GateViolationError(f"Approved Technical Design Blueprint required to start implementation. {reason}")
        return True

    def _verify_blueprint_gate(self, work_item_id: str) -> bool:
        store = get_state_store()
        approvals = store.get("approvals") or {}
        bp = approvals.get("blueprint", {})
        ok, _reason = self._validate_blueprint_approval(bp, work_item_id)
        return ok

    def _validate_blueprint_approval(self, bp: dict[str, Any], work_item_id: str) -> tuple[bool, str]:
        if not work_item_id or work_item_id == "WF-GLOBAL":
            return False, "Missing scoped work_item_id."

        if not isinstance(bp, dict) or bp.get("approved") is not True:
            return False, "Blueprint approval flag is not true."

        bp_path = str(bp.get("path") or bp.get("blueprint_path") or "").strip()
        if not bp_path:
            return False, "Blueprint approval does not include a blueprint path."

        normalized_path = bp_path.replace("\\", "/").lstrip("./")
        if os.path.isabs(bp_path) or normalized_path.startswith("file:"):
            return False, "Blueprint approval path must be project-relative."

        workspace_path = os.path.abspath(os.path.join(self.workspace_root, normalized_path))
        if bp.get("exists") is False or not os.path.exists(workspace_path):
            return False, f"Blueprint file is missing: {normalized_path}."

        record_id = (
            bp.get("work_item_id")
            or bp.get("feature_id")
            or bp.get("issue_id")
            or bp.get("quick_id")
        )
        if record_id and str(record_id) != work_item_id:
            return False, f"Approval belongs to {record_id}, not {work_item_id}."

        path_id = self._extract_work_item_id(normalized_path)
        if path_id and path_id != work_item_id:
            return False, f"Blueprint path belongs to {path_id}, not {work_item_id}."

        content_id = self._extract_work_item_id_from_file(workspace_path)
        if content_id and content_id != work_item_id:
            return False, f"Blueprint content belongs to {content_id}, not {work_item_id}."
        if not (record_id or path_id or content_id):
            return False, "Blueprint approval is not bound to a work item id."

        return True, "Blueprint approval is scoped to this work item."

    @staticmethod
    def _extract_work_item_id(value: str) -> str:
        match = re.search(r"\b(?:FEAT|FIX|QUICK)-\d+\b", value or "")
        return match.group(0) if match else ""

    def _extract_work_item_id_from_file(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                head = f.read(4096)
        except Exception:
            return ""

        for pattern in [
            r"^\s*(?:feature_id|issue_id|quick_id|work_item_id)\s*:\s*[\"']?((?:FEAT|FIX|QUICK)-\d+)",
            r"\b(?:FEAT|FIX|QUICK)-\d+\b",
        ]:
            match = re.search(pattern, head, flags=re.MULTILINE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Workflow Coordinator CLI")
    parser.add_argument("command", choices=["tick"])
    parser.add_argument("--prompt", required=True, type=str)
    parser.add_argument("--work-item", type=str)
    
    args = parser.parse_args()
    
    if args.command == "tick":
        coord = WorkflowCoordinator()
        try:
            res = coord.run_tick(args.prompt, args.work_item)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": str(e)
            }, indent=2, ensure_ascii=False))
            sys.exit(1)
