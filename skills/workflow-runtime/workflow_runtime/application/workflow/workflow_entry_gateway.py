from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator


class WorkflowEntryGateway:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        log_fn: Any = getattr(InfrastructureLocator, "get_logger", None)
        self.logger: Any = log_fn(workspace_root) if callable(log_fn) else None

    def detect_intent(self, request_text: str) -> str:
        """
        Detects the intent of the request.
        Returns one of: 'read_only', 'natural_workflow_request', 'feature_request',
        'bug_fix', 'refactoring', 'migrations', 'architecture_changes',
        'implementation_tasks'.
        """
        request_lower = request_text.lower()

        read_only_keywords = [
            r"^\s*(help|status|doctor|version)\b",
            r"\b(show|read|inspect|explain|describe|summarize)\b",
            r"\b(trạng thái|hướng dẫn|giải thích|đọc|xem)\b",
        ]
        for kw in read_only_keywords:
            if re.search(kw, request_lower):
                return "read_only"

        bug_keywords = [
            r"\bfix\b", r"\bbug\b", r"\berror\b", r"\bissue\b", r"\btypo\b", r"\bmismatch\b", r"\bbroken\b", r"\bregression\b",
            r"\bsửa\b", r"\blỗi\b", r"\bhỏng\b", r"\bsai\b", r"\blệch\b",
        ]
        for kw in bug_keywords:
            if re.search(kw, request_lower):
                return "bug_fix"

        migration_keywords = [r"\bmigration\b", r"\bmigrate\b", r"\bdb schema\b", r"\bupgrade database\b", r"\bdi trú\b", r"\bnâng cấp database\b"]
        for kw in migration_keywords:
            if re.search(kw, request_lower):
                return "migrations"

        arch_keywords = [r"\barchitecture\b", r"\barchitect\b", r"\badr\b", r"\bdesign pattern\b", r"\bkiến trúc\b", r"\bthiết kế hệ thống\b"]
        for kw in arch_keywords:
            if re.search(kw, request_lower):
                return "architecture_changes"

        refactor_keywords = [r"\brefactor\b", r"\bclean\b", r"\bsimplify\b", r"\brewrite\b", r"\btái cấu trúc\b", r"\bdọn\b", r"\bviết lại\b"]
        for kw in refactor_keywords:
            if re.search(kw, request_lower):
                return "refactoring"

        task_keywords = [r"\btask\b", r"\bimplement code\b", r"\bwrite code\b", r"\bcoding\b", r"\bcode\b", r"\btriển khai\b", r"\bimplement\b"]
        for kw in task_keywords:
            if re.search(kw, request_lower):
                return "implementation_tasks"

        feat_keywords = [
            r"\badd\b", r"\bfeature\b", r"\bnew\b", r"\bimplement\b",
            r"\bcreate\b", r"\bmodify\b", r"\bdelete\b", r"\btest\b",
            r"\bbuild\b", r"\brelease\b", r"\bpublish\b", r"feat-\d+", r"quick-\d+",
            r"\bthêm\b", r"\btạo\b", r"\bnâng cấp\b", r"\bcập nhật\b", r"\bkiểm tra\b", r"\bchạy\b", r"\bphát hành\b",
        ]
        for kw in feat_keywords:
            if re.search(kw, request_lower):
                return "feature_request"

        return "natural_workflow_request"

    def _suggest_next_skill(self, intent: str) -> dict[str, Any]:
        if intent == "read_only":
            return {"skill": "environment-health", "command": "status"}
        if intent == "bug_fix":
            return {"skill": "quick-fix", "command": "fix"}
        if intent in {"migrations", "architecture_changes", "refactoring"}:
            return {"skill": "brainstorming", "command": "brainstorm"}
        return {"skill": "brainstorming", "command": "brainstorm"}

    def _run_coordinator_tick(self, workflow_id: str, session_id: str) -> dict[str, Any]:
        from workflow_runtime.application.workflow.coordinator_service import (
            WorkflowCoordinatorService)

        state_root = os.path.join(self.workspace_root, ".agents", "state")
        adapter_cls: Any = getattr(InfrastructureLocator, "StateStoreAdapter", None)
        repository: Any = adapter_cls(state_root) if callable(adapter_cls) else None
        if repository is None:
            return {
                "status": "degraded",
                "workflow_id": workflow_id,
                "checkpoint": 1,
                "active_phase": "brainstorming",
                "warning": "state_store_adapter_unavailable",
            }
        service = WorkflowCoordinatorService(repository)
        result = service.tick(dry_run=False, session_id=session_id)
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "checkpoint": result.checkpoint,
            "active_phase": result.active_phase,
        }

    def generate_request_id(self) -> str:
        """
        Generates a sequential request ID by counting existing workflow.request.received events.
        """
        try:
            read_fn: Any = getattr(self.logger, "read_all", None)
            events: Any = read_fn() if callable(read_fn) else []
            req_count = sum(1 for e in cast(list[Any], events) if isinstance(e, dict) and cast(dict[str, Any], e).get("event_type") == "workflow.request.received")
            return f"REQ-{req_count + 1:03d}"
        except Exception:
            import uuid
            return f"REQ-{uuid.uuid4().hex[:6].upper()}"

    def extract_workflow_id(self, request_text: str) -> str:
        """
        Extracts FEAT-xxx or QUICK-xxx from text, or returns FEAT-AUTO.
        """
        m = re.search(r"\b(feat-\d+|quick-\d+)\b", request_text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        return "FEAT-AUTO"

    def handle_request(self, request_text: str, source: str | None = None, session_id: str | None = None) -> dict[str, Any]:
        """
        Receives an engineering/chat request and routes accordingly.
        Redirects routing to the new WorkflowCoordinator tick engine.
        """
        intent = self.detect_intent(request_text)
        req_id = self.generate_request_id()
        active_session_id = session_id or "default_session"

        emit_fn: Any = getattr(self.logger, "emit", None)

        if callable(emit_fn):
            emit_fn(
                "workflow.request.received",
                {"request_id": req_id, "intent": intent, "request_text": request_text, "source": source or "system", "session_id": active_session_id}
            )

        workflow_id = self.extract_workflow_id(request_text)
        if workflow_id == "FEAT-AUTO":
            max_num = 0
            for d in ["docs/brainstorming", "docs/blueprints", "docs/plans", "docs/verification"]:
                d_path = os.path.join(self.workspace_root, d)
                if os.path.exists(d_path):
                    for _root, _dirs, files in os.walk(d_path):
                        for f in files:
                            match = re.search(r"FEAT-(\d+)", f)
                            if match:
                                num = int(match.group(1))
                                if num > max_num:
                                    max_num = num
            feat_id = max_num + 1 if max_num > 0 else 312
            workflow_id = f"FEAT-{feat_id:03d}"

        coord_res = self._run_coordinator_tick(workflow_id, active_session_id)
        entry_phase = "status" if intent == "read_only" else "brainstorming"
        next_skill_info = self._suggest_next_skill(intent)

        if callable(emit_fn):
            emit_fn("workflow.created", {"request_id": req_id, "workflow_id": workflow_id, "intent": intent, "status": "CREATED", "next_phase": entry_phase, "source": source or "system", "session_id": active_session_id})
            emit_fn("workflow.started", {"request_id": req_id, "workflow_id": workflow_id})
            emit_fn("workflow.phase.started", {"request_id": req_id, "workflow_id": workflow_id, "phase": entry_phase})
            emit_fn("skill.selected", {"request_id": req_id, "workflow_id": workflow_id, "skill": next_skill_info["skill"], "command": next_skill_info["command"]})
            emit_fn("skill.started", {"request_id": req_id, "workflow_id": workflow_id, "skill": next_skill_info["skill"], "command": next_skill_info["command"]})

        if self.workspace_root in ("", "."):
            state_dir = os.path.join(".agents", "state")
        else:
            state_dir = os.path.join(self.workspace_root, ".agents", "state")
        os.makedirs(state_dir, exist_ok=True)
        wf_path = os.path.join(state_dir, "workflow.json")
        wf_data: dict[str, Any] = {}
        if os.path.exists(wf_path):
            try:
                with open(wf_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        wf_data = cast(dict[str, Any], loaded)
            except Exception:
                pass
        wf_data.update({
            "active_workflow": workflow_id,
            "active_phase": entry_phase,
            "checkpoint": coord_res.get("checkpoint") or 1,
            "status": "IN_PROGRESS",
            "session_id": active_session_id,
            "work_item": {
                "type": "FEAT" if workflow_id.startswith("FEAT") else "QUICK",
                "id": workflow_id,
                "title": request_text
            },
            "suggested_next_skill": next_skill_info["skill"],
            "suggested_next_command": next_skill_info["command"]
        })
        with open(wf_path, "w", encoding="utf-8") as f:
            json.dump(wf_data, f, indent=2, ensure_ascii=False)

        ctx_path = os.path.join(state_dir, "context.json")
        ctx_data: dict[str, Any] = {}
        if os.path.exists(ctx_path):
            try:
                with open(ctx_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        ctx_data = cast(dict[str, Any], loaded)
            except Exception:
                pass
        ctx_data.update({
            "work_item_id": workflow_id,
            "workflow_id": workflow_id,
            "phase": entry_phase,
            "checkpoint": coord_res.get("checkpoint") or 1,
            "authorization": {
                "allowed_phases": ["discovery", "brainstorming", "planning", "blueprint", "implementation", "debug", "verification"]
            }
        })
        with open(ctx_path, "w", encoding="utf-8") as f:
            json.dump(ctx_data, f, indent=2, ensure_ascii=False)

        rt_path = os.path.join(state_dir, "runtime.json")
        rt_data: dict[str, Any] = {}
        if os.path.exists(rt_path):
            try:
                with open(rt_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        rt_data = cast(dict[str, Any], loaded)
            except Exception:
                pass
        rt_data.update({
            "status": "in_progress" if coord_res.get("status") == "success" else "waiting_input",
            "current_skill": next_skill_info["skill"],
            "current_command": next_skill_info["command"],
            "checkpoint": coord_res.get("checkpoint") or 1,
            "updated_at": datetime.now().astimezone().isoformat()
        })
        with open(rt_path, "w", encoding="utf-8") as f:
            json.dump(rt_data, f, indent=2, ensure_ascii=False)

        os.environ["AIWF_WORKFLOW_ID"] = workflow_id
        os.environ["AIWF_EXECUTION_MODE"] = "workflow"
        os.environ["AIWF_CURRENT_PHASE"] = entry_phase

        return {
            "status": "ROUTED",
            "request_id": req_id,
            "intent": intent,
            "workflow_id": workflow_id,
            "workflow": "standard-development",
            "execution_mode": "workflow",
            "current_phase": entry_phase,
            "next_skill": next_skill_info["skill"],
            "source": source or "system",
            "session_id": active_session_id
        }


__all__ = ["WorkflowEntryGateway"]
