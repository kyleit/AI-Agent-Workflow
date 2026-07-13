# context_firewall.py
import os
from pathlib import Path
from typing import Any

class ProjectContextViolationError(ValueError):
    pass

class ContextFirewall:
    def __init__(self, project_scope: dict[str, Any]):
        self.project_scope = project_scope
        self.project_id = project_scope.get("project_id", "unknown")
        self.workspace_root = os.path.abspath(project_scope.get("workspace_root", "."))
        self.git_root = os.path.abspath(project_scope.get("git_root", "."))
        self.allow_cross_project = project_scope.get("allow_cross_project_context", False)
        self.resolved_paths_cache: dict[str, bool] = {}

    def _is_sub_path(self, parent: str, child: str) -> bool:
        try:
            parent_path = Path(os.path.abspath(parent)).resolve()
            child_path = Path(os.path.abspath(child)).resolve()
            return parent_path in child_path.parents or parent_path == child_path
        except Exception:
            return False

    def validate_context_path(self, file_path: str) -> bool:
        if self.allow_cross_project:
            return True
            
        if file_path in self.resolved_paths_cache:
            if not self.resolved_paths_cache[file_path]:
                raise ProjectContextViolationError(f"Context violation: path '{file_path}' is blocked.")
            return True
            
        abs_path = os.path.abspath(file_path)
        
        # Special allowance for App Data Directory, temporary brain files, config and scratch files
        is_valid = self._is_sub_path(self.workspace_root, abs_path) or self._is_sub_path(self.git_root, abs_path)
        if not is_valid:
            abs_normalized = abs_path.replace("\\", "/")
            if "/.gemini/antigravity-ide" in abs_normalized or "/.gemini/config" in abs_normalized:
                is_valid = True
                
        self.resolved_paths_cache[file_path] = is_valid
        if not is_valid:
            raise ProjectContextViolationError(f"Context violation: path '{file_path}' is outside active project scope.")
        return True

    def filter_rag_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.allow_cross_project:
            return results
        filtered = []
        for item in results:
            proj_id = item.get("metadata", {}).get("project_id") if isinstance(item, dict) else None
            if not proj_id or proj_id == self.project_id:
                filtered.append(item)
        return filtered

    def validate_conversation(self, history: list[dict[str, Any]], active_project_id: str) -> bool:
        if self.allow_cross_project:
            return True
        for step in history:
            if not isinstance(step, dict):
                continue
            proj_id = step.get("project_id") or step.get("metadata", {}).get("project_id")
            if proj_id and proj_id != active_project_id:
                return False
        return True
