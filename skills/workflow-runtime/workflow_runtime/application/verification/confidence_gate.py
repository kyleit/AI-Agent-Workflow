# confidence_gate.py
from __future__ import annotations

import glob
import json
import os
import re
from typing import Any, cast


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
    def calculate_confidence(phase: str, workspace_root: str = ".") -> tuple[float, list[str]]:
        """
        Calculates confidence score (0-100) and identifies gaps for a given phase.
        """
        state_dir = os.path.join(workspace_root, ".agents", "state")
        workflow_path = os.path.join(state_dir, "workflow.json")

        active_id = "unknown"
        if os.path.exists(workflow_path):
            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    wf_raw = json.load(f)
                    if isinstance(wf_raw, dict):
                        wf = cast(dict[str, Any], wf_raw)
                        work_item_raw = wf.get("work_item")
                        if isinstance(work_item_raw, dict):
                            work_item = cast(dict[str, Any], work_item_raw)
                            active_id = str(work_item.get("id", "unknown"))
            except Exception:
                pass

        content = ""
        filepath: str | None = None

        if phase == "brainstorm":
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
        gaps: list[str] = []

        req_sections = ConfidenceGate.REQUIRED_SECTIONS.get(phase, [])
        for section in req_sections:
            header_pattern = rf"(?i)(#+|=+|-+|\*\*)\s*{re.escape(section)}"
            if not re.search(header_pattern, content):
                score -= 15.0
                gaps.append(f"Missing required section: '{section}'")

        for kw in ConfidenceGate.AMBIGUOUS_KEYWORDS:
            matches = re.findall(kw, content, re.IGNORECASE)
            if matches:
                deduction = len(matches) * 5.0
                score -= deduction
                gaps.append(f"Found ambiguous keyword '{kw}' ({len(matches)} occurrences)")

        if phase in ["planning", "blueprint"]:
            if "Dependency" in content:
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
    def _find_matching_file(patterns: list[str]) -> str:
        for pat in patterns:
            files = glob.glob(pat)
            if files:
                return files[0]
        return ""


__all__ = ["ConfidenceGate"]
