# artifact_governance.py
import os
import re
from typing import Dict, Any, List

# Predefined standard storage policy mappings
APPROVED_MAPPINGS: Dict[str, str] = {
    "brainstorming": "docs/brainstorming",
    "planning": "docs/planning",
    "architecture": "docs/architecture",
    "blueprint": "docs/blueprints",
    "implementation": "docs/implementation",
    "verification": "docs/verification",
    "release": "docs/release",
    "report": "docs/reports",
    "operations": "docs/operations"
}

class ArtifactGovernance:
    @staticmethod
    def normalize_path(filepath: str, workspace_root: str = ".") -> str:
        # Resolve absolute paths to workspace-relative paths if possible
        abs_workspace = os.path.abspath(workspace_root)
        abs_file = os.path.abspath(filepath)
        
        if abs_file.startswith(abs_workspace):
            rel_path = os.path.relpath(abs_file, abs_workspace)
        else:
            rel_path = filepath
            
        return rel_path.replace("\\", "/")

    @staticmethod
    def validate_artifact_path(filepath: str, expected_type: str, workspace_root: str = ".") -> dict:
        if not filepath:
            return {
                "status": "failure",
                "code": "MISSING_PATH",
                "summary": "No file path provided."
            }

        normalized = ArtifactGovernance.normalize_path(filepath, workspace_root)
        
        # Check project root constraints: Forbidden to create Markdown artifacts in root
        if "/" not in normalized and normalized.endswith(".md"):
            return {
                "status": "failure",
                "code": "ARTIFACT_LOCATION_VIOLATION",
                "summary": f"Creating workflow artifacts in project root is forbidden: '{normalized}'."
            }

        # Check against approved mappings
        expected_dir = APPROVED_MAPPINGS.get(expected_type.lower())
        if not expected_dir:
            return {
                "status": "failure",
                "code": "INVALID_ARTIFACT_TYPE",
                "summary": f"Unknown artifact type: '{expected_type}'."
            }

        # Verify correct directory structure prefix
        if not normalized.startswith(expected_dir + "/"):
            return {
                "status": "failure",
                "code": "ARTIFACT_LOCATION_VIOLATION",
                "summary": f"Artifact '{normalized}' of type '{expected_type}' must be located in approved folder '{expected_dir}/'."
            }

        # Filename convention checks
        filename = os.path.basename(normalized)
        
        if expected_type.lower() == "brainstorming":
            if not (filename.startswith("FEAT-") or filename.startswith("FIX-")) or not filename.endswith(".md"):
                return {
                    "status": "failure",
                    "code": "FILENAME_CONVENTION_VIOLATION",
                    "summary": f"Brainstorming filename '{filename}' must follow FEAT-xxx.md or FIX-xxx.md format."
                }
        elif expected_type.lower() == "planning":
            if not (filename.startswith("FEAT-") or filename.startswith("FIX-")) or "_plan" not in filename or not (filename.endswith(".md") or filename.endswith(".json")):
                return {
                    "status": "failure",
                    "code": "FILENAME_CONVENTION_VIOLATION",
                    "summary": f"Planning filename '{filename}' must follow FEAT-xxx_plan.md format."
                }
        elif expected_type.lower() == "blueprint":
            if not (filename.startswith("FEAT-") or filename.startswith("FIX-")) or "_blueprint" not in filename or not (filename.endswith(".md") or filename.endswith(".json")):
                return {
                    "status": "failure",
                    "code": "FILENAME_CONVENTION_VIOLATION",
                    "summary": f"Blueprint filename '{filename}' must follow FEAT-xxx_blueprint.md format."
                }
        elif expected_type.lower() == "report":
            if not (filename.startswith("FEAT-") or filename.startswith("FIX-") or "report" in filename.lower()) or not filename.endswith(".md"):
                return {
                    "status": "failure",
                    "code": "FILENAME_CONVENTION_VIOLATION",
                    "summary": f"Report filename '{filename}' must be a markdown file with a valid name format."
                }

        return {
            "status": "success",
            "code": "OK",
            "summary": f"Artifact path '{normalized}' verified successfully."
        }

    @staticmethod
    def scan_root_violations(workspace_root: str = ".") -> List[str]:
        violations: List[str] = []
        for item in os.listdir(workspace_root):
            path = os.path.join(workspace_root, item)
            if os.path.isfile(path) and item.endswith(".md"):
                # Exclude canonical system files
                if item in ["README.md", "CHANGELOG.md", "AGENTS.md", "AI_RULES.md", "SKILLS.md", "USAGE.md", "INSTALL.md", "LICENSE"]:
                    continue
                # Found a workflow artifact violation in root
                violations.append(item)
        return violations
