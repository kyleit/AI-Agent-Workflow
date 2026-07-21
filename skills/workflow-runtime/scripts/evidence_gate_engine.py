# evidence_gate_engine.py
import os
from typing import Any, Dict, List

class EvidenceGateEngine:
    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = workspace_root

    def evaluate_gate(self, gate_name: str, evidence: Dict[str, Any]) -> str:
        # Check physical folder artifacts as required by FEAT-304
        if evidence.get("workflow_mode") == "autonomous":
            brainstorming_dir = os.path.join(self.workspace_root, "docs", "brainstorming")
            planning_dir = os.path.join(self.workspace_root, "docs", "plans")
            blueprints_dir = os.path.join(self.workspace_root, "docs", "blueprints")
            
            # Brainstorming folder check
            if not os.path.exists(brainstorming_dir) or not any(f.endswith(".md") for f in os.listdir(brainstorming_dir)):
                return "FAIL"
            # Planning folder check
            if gate_name != "Gate1_PlanApproval" and (not os.path.exists(planning_dir) or not any(f.endswith(".md") for f in os.listdir(planning_dir))):
                return "FAIL"
            # Blueprints folder check
            if gate_name == "Gate3_ReleaseApproval" and (not os.path.exists(blueprints_dir) or not any(f.endswith(".md") for f in os.listdir(blueprints_dir))):
                return "FAIL"

        # Decisions: "PASS" | "FAIL" | "BLOCKED"
        if gate_name == "Gate1_PlanApproval":
            # Plan approval requires implementation plan file and project profile
            plan_path = os.path.join(self.workspace_root, evidence.get("plan_file", ""))
            profile_path = os.path.join(self.workspace_root, evidence.get("profile_file", ""))
            
            if not os.path.exists(plan_path) or not os.path.exists(profile_path):
                return "BLOCKED"
                
            # Simulate check for human approval flag in plan file
            with open(plan_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "PLAN APPROVED" in content or "request_feedback: false" in content or evidence.get("user_approved"):
                    return "PASS"
            return "FAIL"

        elif gate_name == "Gate2_BlueprintApproval":
            blueprint_path = os.path.join(self.workspace_root, evidence.get("blueprint_file", ""))
            if not os.path.exists(blueprint_path):
                return "BLOCKED"
                
            with open(blueprint_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "BLUEPRINT APPROVED" in content or evidence.get("user_approved"):
                    return "PASS"
            return "FAIL"

        elif gate_name == "Gate3_ReleaseApproval":
            candidate_path = os.path.join(self.workspace_root, evidence.get("release_candidate_file", ""))
            test_log_path = os.path.join(self.workspace_root, evidence.get("test_log_file", ""))
            
            if not os.path.exists(candidate_path) or not os.path.exists(test_log_path):
                return "BLOCKED"
                
            with open(test_log_path, "r", encoding="utf-8") as f:
                logs = f.read()
                # If there are any failed tests, fail the gate
                if "FAILED" in logs or "error" in logs.lower():
                    return "FAIL"
                    
            if evidence.get("user_approved"):
                return "PASS"
            return "FAIL"

        return "BLOCKED"
