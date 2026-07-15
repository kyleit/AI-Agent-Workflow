# confidence_gate.py
import os
import re
import json
from typing import Tuple, List, Dict, Any

class ConfidenceGate:
    """
    Computes an objective confidence score for workflow phases:
    brainstorm, planning, and blueprint.
    """

    AMBIGUOUS_KEYWORDS = [
        r"\bTODO\b", r"\bTBD\b", r"\bN/A\b", r"\bguess\b", 
        r"\bapproximate\b", r"\bunresolved\b", r"\bconflicting\b",
        r"\bplaceholder\b", r"\bnot clear\b", r"\bassumed\b"
    ]

    REQUIRED_SECTIONS = {
        "brainstorm": [
            "Feature Goal", "Scope Boundary", "Trigger", "Success Metrics"
        ],
        "planning": [
            "Proposed Changes", "Verification Plan", "Dependency Contract", "Error Matrix"
        ],
        "blueprint": [
            "Proposed Code Changes", "Interface & Data Contracts", "Validation Rules", "Verification & Test Plan"
        ]
    }

    @staticmethod
    def calculate_confidence(phase: str, workspace_root: str = ".") -> Tuple[float, List[str]]:
        """
        Calculates confidence score (0-100) and identifies gaps for a given phase.
        """
        state_dir = os.path.join(workspace_root, ".agents", "state")
        context_path = os.path.join(state_dir, "context.json")
        workflow_path = os.path.join(state_dir, "workflow.json")

        active_id = "unknown"
        if os.path.exists(workflow_path):
            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    wf = json.load(f)
                    active_id = wf.get("work_item", {}).get("id", "unknown")
            except Exception:
                pass

        # Try to find corresponding document
        content = ""
        filepath = None

        if phase == "brainstorm":
            # Check docs/quick/ or docs/brainstorming/
            patterns = [
                os.path.join(workspace_root, "docs", "quick", f"{active_id}_*.md"),
                os.path.join(workspace_root, "docs", "brainstorming", f"{active_id}_*.md")
            ]
            filepath = ConfidenceGate._find_matching_file(patterns)
        elif phase == "planning":
            patterns = [
                os.path.join(workspace_root, "docs", "plans", f"{active_id}_*.md")
            ]
            filepath = ConfidenceGate._find_matching_file(patterns)
        elif phase == "blueprint":
            patterns = [
                os.path.join(workspace_root, "docs", "designs", f"{active_id}_*_blueprint.md"),
                os.path.join(workspace_root, "docs", "designs", f"{active_id}_blueprint.md")
            ]
            filepath = ConfidenceGate._find_matching_file(patterns)

        if not filepath or not os.path.exists(filepath):
            return 0.0, [f"Missing artifact file for phase '{phase}' (Work Item: {active_id})"]

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return 0.0, [f"Error reading artifact file {filepath}: {str(e)}"]

        score = 100.0
        gaps = []

        # 1. Check required sections
        req_sections = ConfidenceGate.REQUIRED_SECTIONS.get(phase, [])
        for section in req_sections:
            # Simple header match (e.g. ## Section or # Section or **Section**)
            header_pattern = rf"(?i)(#+|=+|-+|\*\*)\s*{re.escape(section)}"
            if not re.search(header_pattern, content):
                score -= 15.0
                gaps.append(f"Missing required section: '{section}'")

        # 2. Check ambiguity & assumptions keywords
        for kw in ConfidenceGate.AMBIGUOUS_KEYWORDS:
            matches = re.findall(kw, content, re.IGNORECASE)
            if matches:
                deduction = len(matches) * 5.0
                score -= deduction
                gaps.append(f"Found ambiguous keyword '{kw}' ({len(matches)} occurrences)")

        # 3. Check dependency completeness (for planning & blueprint)
        if phase in ["planning", "blueprint"]:
            if "Dependency" in content:
                # Check if dependency list is empty or generic
                dep_contract = re.search(rf"(?i)dependency\s*contract.*", content)
                if dep_contract and "TODO" in dep_contract.group(0):
                    score -= 10.0
                    gaps.append("Incomplete dependency contracts")
            else:
                score -= 10.0
                gaps.append("Missing dependency verification information")

        score = max(0.0, min(100.0, score))
        return score, gaps

    @staticmethod
    def _find_matching_file(patterns: List[str]) -> str:
        import glob
        for pat in patterns:
            files = glob.glob(pat)
            if files:
                return files[0]
        return ""


class ClarificationGateException(Exception):
    def __init__(self, message: str, gaps: List[str]):
        super().__init__(message)
        self.gaps = gaps


class ClarificationGate:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root

    def _generate_clarification_prompt(self, gaps: List[str]) -> str:
        gaps_list = "\n".join(f"- {g}" for g in gaps)
        return (
            f"The confidence score is below 85.0. Execution is blocked due to the following gaps:\n"
            f"{gaps_list}\n"
            f"Please clarify or provide the missing requirements to proceed."
        )

    def check_readiness_and_route(self, phase: str, score: float, gaps: List[str]) -> dict:
        from state_store import get_state_store
        store = get_state_store()
        workflow = store.get("workflow") or {}
        
        if score < 85.0:
            workflow["status"] = "BLOCKED"
            workflow["active_phase"] = phase
            store.set("workflow", workflow)
            
            prompt = self._generate_clarification_prompt(gaps)
            raise ClarificationGateException(prompt, gaps)
        else:
            workflow["status"] = "success"
            normalized_phase = phase.lower().strip()
            if normalized_phase in ["brainstorming", "brainstorm"]:
                workflow["active_phase"] = "planning"
                workflow["suggested_next_skill"] = "brainstorming-to-plan"
                workflow["suggested_next_command"] = "plan"
            elif normalized_phase == "planning":
                workflow["active_phase"] = "blueprint"
                workflow["suggested_next_skill"] = "plan-to-blueprint"
                workflow["suggested_next_command"] = "blueprint"
            elif normalized_phase == "blueprint":
                workflow["active_phase"] = "implementation"
                workflow["suggested_next_skill"] = "blueprint-to-implementation"
                workflow["suggested_next_command"] = "implement"
                
            store.set("workflow", workflow)
            
            return {
                "status": "success",
                "phase": workflow.get("active_phase"),
                "next_skill": workflow.get("suggested_next_skill")
            }
