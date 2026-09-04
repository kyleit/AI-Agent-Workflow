from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator
from workflow_runtime.infrastructure.memory.common import read_json_safe, read_text_safe, write_json_safe


@dataclass(frozen=True)
class MemoryReadiness:
    status: str
    files_changed: int = 0
    summary_path: str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentContext:
    summary: str
    query: str
    evidence: tuple[str, ...] = ()
    freshness: str = "UNVERIFIED"
    context_path: str | None = None
    provider: str = "none"
    rag_status: str = "unavailable"
    memory_action: str = "cache"
    memory_receipt: str = ".agents/state/memory-preflight.json"
    retrieval: tuple[dict[str, Any], ...] = ()
    next_action: str = "read current source authority"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextPreflightRequest:
    request: str
    workspace_root: str
    work_item: str = ""
    max_results: int = 5
    allow_rebuild: bool = False


def _summary_path(root: Path) -> Path:
    return root / ".agents" / "memory" / "project-summary.md"


def bootstrap_project_memory(root: Path, mode: str = "compact_ai_context") -> dict[str, object]:
    from workflow_runtime.infrastructure.memory.bootstrap import run_bootstrap
    use_remote_ai = os.environ.get("AIWF_MEMORY_AI_SYNTHESIS", "").lower() in {"1", "true", "yes"}
    return cast(dict[str, object], run_bootstrap(str(root), enable_ai=use_remote_ai))


def update_project_memory_from_git_diff(root: Path) -> dict[str, object]:
    from workflow_runtime.infrastructure.memory.update import run_update
    return cast(dict[str, object], run_update(target_dir=str(root)))


def ensure_project_memory(root: Path | str) -> MemoryReadiness:
    root_path = Path(root)
    summary = _summary_path(root_path)
    if not summary.exists():
        result = bootstrap_project_memory(root_path, mode="compact_ai_context")
        status = "bootstrapped" if str(result.get("status")) == "success" else "degraded"
        return MemoryReadiness(status, summary_path=str(summary), details=dict(result))
    result = update_project_memory_from_git_diff(root_path)
    changed = int(result.get("data", {}).get("files_changed_count", 0)) if isinstance(result.get("data"), dict) else 0
    status = "updated" if str(result.get("status")) == "success" else "degraded"
    return MemoryReadiness(status, changed, str(summary), dict(result))


def build_agent_context(root: Path | str, query: str, memory_readiness: MemoryReadiness | None = None) -> AgentContext:
    root_path = Path(root)
    summary = read_text_safe(_summary_path(root_path))
    pack = build_context_preflight(query, root_path, memory_readiness=memory_readiness)
    evidence = [str(item.get("file", "")) for item in pack["evidence"] if item.get("file")]
    return AgentContext(
        summary=summary,
        query=query,
        evidence=tuple(evidence[:8]),
        freshness=str(pack["decision"]["freshness"]),
        context_path=str(pack["manifest"].get("path")) if pack["manifest"].get("path") else None,
        provider=str(pack["decision"].get("provider", "none")),
        rag_status=str(pack.get("rag_status", "unavailable")),
        memory_action=str(pack.get("memory_action", "cache")),
        memory_receipt=str(pack.get("memory_receipt", ".agents/state/memory-preflight.json")),
        retrieval=tuple(pack["evidence"]),
        next_action=str(pack["next_action"]),
        warnings=tuple(pack["warnings"]),
    )


def build_context_preflight(
    request: str,
    root: Path | str,
    work_item: str = "",
    max_results: int = 5,
    allow_rebuild: bool = False,
    memory_readiness: MemoryReadiness | None = None,
) -> dict[str, Any]:
    """Build the bounded context pack every Agent entrypoint receives first."""
    root_path = Path(root).resolve()
    manifest_path = root_path / ".agents" / "memory" / "project-context.json"
    from workflow_runtime.infrastructure.memory.context_manifest import load_context_manifest, manifest_freshness
    manifest = load_context_manifest(manifest_path) or {}
    if not _summary_path(root_path).exists() or not manifest:
        memory_readiness = ensure_project_memory(root_path)
        manifest = load_context_manifest(manifest_path) or {}
    freshness = manifest_freshness(root_path, manifest)
    warnings: list[str] = []
    if not manifest:
        warnings.append("project_context_manifest_missing")
    elif freshness == "STALE":
        warnings.append("project_context_stale_targeted_source_refresh_required")
    rag_searcher_cls: Any = getattr(InfrastructureLocator, "RAGSearcher", None)
    if request.strip() and callable(rag_searcher_cls):
        retrieval = rag_searcher_cls(root_dir=root_path).execute_search(request)
    else:
        retrieval = {
            "results": [],
            "selected_provider": "none",
            "provider_health": [],
            "fallback_reason": "rag_adapter_unavailable",
        }
    evidence = [item for item in retrieval.get("results", []) if isinstance(item, dict)][:max(1, max_results)]
    provider = str(retrieval.get("selected_provider", "none"))
    health = [item for item in retrieval.get("provider_health", []) if isinstance(item, dict)]
    health_by_provider = {str(item.get("provider")): item for item in health}
    local_ready = any(str(item.get("state")) == "READY" for item in health if str(item.get("provider")) != "qdrant")
    qmd_ready = str(health_by_provider.get("qmd", {}).get("state", "")) == "READY"
    rag_status = "unavailable"
    if provider == "qmd" and qmd_ready:
        rag_status = "ready"
    elif provider != "none" and local_ready:
        rag_status = "fallback" if not qmd_ready else "ready"
    elif provider == "none" and local_ready:
        rag_status = "fallback"
    memory_state = read_json_safe(root_path / ".agents" / "memory" / "memory-state.json", {})
    memory_action = "bootstrap" if memory_readiness and memory_readiness.status == "bootstrapped" else "sync" if memory_readiness and memory_readiness.status == "updated" else "cache"
    next_action = "read only the cited source anchors and verify current source hashes"
    if freshness in {"STALE", "UNVERIFIED"}:
        next_action = "refresh project memory/index, then read only the cited current source anchors"
    decision = {
        "decision": "REFRESH_REQUIRED" if freshness in {"STALE", "UNVERIFIED"} else "RETRIEVAL_READY",
        "freshness": freshness,
        "provider": provider,
        "required_source_reads": [str(item.get("anchor") or item.get("file")) for item in evidence],
        "blocking_findings": [],
    }
    receipt = {
        "schema_version": "aiwf.context-preflight.v1",
        "request": request,
        "work_item": work_item,
        "memory_action": memory_action,
        "memory_status": memory_readiness.status if memory_readiness else "cached",
        "memory_revision": memory_state.get("last_git_hash") if isinstance(memory_state, dict) else None,
        "rag_provider": provider,
        "rag_status": rag_status,
        "retrieval_count": len(evidence),
        "freshness": freshness,
        "source_authority": "current_worktree",
        "generated_at": datetime.now().astimezone().isoformat(),
        "evidence": [str(item.get("anchor") or item.get("file")) for item in evidence],
    }
    receipt_path = root_path / ".agents" / "state" / "memory-preflight.json"
    try:
        write_json_safe(receipt_path, receipt)
    except OSError as exc:
        warnings.append(f"memory_preflight_receipt_write_failed: {exc}")
    return {
        "request": request,
        "work_item": work_item,
        "manifest": {"path": manifest_path.relative_to(root_path).as_posix(), **manifest},
        "summary": read_text_safe(_summary_path(root_path), max_chars=12000),
        "evidence": evidence,
        "source_authority": "current source files; generated memory is retrieval/navigation only",
        "next_action": next_action,
        "warnings": warnings + ([str(retrieval.get("fallback_reason"))] if retrieval.get("fallback_reason") else []),
        "decision": decision,
        "provider_health": retrieval.get("provider_health", []),
        "memory_action": memory_action,
        "memory_receipt": ".agents/state/memory-preflight.json",
        "rag_status": rag_status,
        "retrieval_count": len(evidence),
        "allow_rebuild": allow_rebuild,
    }


class WorkflowEntryGateway:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        log_fn: Any = getattr(InfrastructureLocator, "get_logger", None)
        if callable(log_fn):
            self.logger: Any = log_fn(workspace_root)
        else:
            from workflow_runtime.infrastructure.events.event_logger import EventLogger
            self.logger = EventLogger(workspace_root)

    def discover_project_profile(self) -> dict[str, Any]:
        """Run project discovery in the requested workspace and return its profile."""
        from workflow_runtime.application.system.project_discovery import run_discovery

        original_cwd = os.getcwd()
        target = os.path.abspath(self.workspace_root)
        try:
            os.chdir(target)
            discovery = run_discovery()
            profile_path = os.path.join(target, ".agents", "project-profile.json")
            with open(profile_path, "r", encoding="utf-8") as stream:
                profile = json.load(stream)
        finally:
            os.chdir(original_cwd)
        return {"status": discovery.get("status", "success"), "profile": profile, "discovery": discovery}

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
        Extracts an explicit work item ID, or returns a marker for generation.
        """
        m = re.search(r"\b(feat-\d+|fix-\d+|quick-\d+)\b", request_text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        return "FEAT-AUTO"

    def _next_generated_workflow_id(self) -> str:
        """Allocate a new feature ID without inheriting the active workflow."""
        max_num = 0
        scan_roots = [
            os.path.join(self.workspace_root, "docs"),
            os.path.join(self.workspace_root, ".agents", "state"),
        ]
        for scan_root in scan_roots:
            if not os.path.exists(scan_root):
                continue
            for root, _dirs, files in os.walk(scan_root):
                for filename in files:
                    match = re.search(r"FEAT-(\d+)", filename, re.IGNORECASE)
                    if match:
                        max_num = max(max_num, int(match.group(1)))
        return f"FEAT-{max_num + 1:03d}"

    def _read_only_status(self, request_id: str, source: str | None, session_id: str) -> dict[str, Any]:
        state_dir = os.path.join(self.workspace_root, ".agents", "state")
        path = os.path.join(state_dir, "workflow.json")
        state: dict[str, Any] = {}
        try:
            with open(path, "r", encoding="utf-8") as stream:
                loaded = json.load(stream)
            if isinstance(loaded, dict):
                state = cast(dict[str, Any], loaded)
        except (OSError, ValueError):
            pass
        return {
            "status": "READ_ONLY",
            "request_id": request_id,
            "intent": "read_only",
            "workflow_id": state.get("active_workflow"),
            "current_phase": state.get("active_phase"),
            "next_skill": state.get("suggested_next_skill"),
            "next_command": state.get("suggested_next_command"),
            "source": source or "system",
            "session_id": session_id,
            "side_effects": [],
        }

    def _write_workflow_state(self, state_dir: str, patch: dict[str, Any], *, mutation: bool) -> None:
        path = os.path.join(state_dir, "workflow.json")
        current: dict[str, Any] = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as stream:
                    loaded = json.load(stream)
                if isinstance(loaded, dict):
                    current = cast(dict[str, Any], loaded)
            except (OSError, ValueError):
                pass
        response = dict(current)
        if mutation:
            response.update(patch)
        else:
            response.update({"read_only": True, "requested_action": patch.get("requested_action", "status")})
        os.makedirs(state_dir, exist_ok=True)
        temporary = f"{path}.tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(response, stream, indent=2, ensure_ascii=False)
        os.replace(temporary, path)

    def handle_request(self, request_text: str, source: str | None = None, session_id: str | None = None) -> dict[str, Any]:
        """
        Receives an engineering/chat request and routes accordingly.
        Redirects routing to the new WorkflowCoordinator tick engine.
        """
        intent = self.detect_intent(request_text)
        req_id = self.generate_request_id()
        active_session_id = session_id or "default_session"

        if intent == "read_only":
            return self._read_only_status(req_id, source, active_session_id)

        memory_readiness = ensure_project_memory(self.workspace_root)
        agent_context = build_agent_context(self.workspace_root, request_text, memory_readiness)
        emit_fn: Any = getattr(self.logger, "emit", None)

        if callable(emit_fn):
            emit_fn(
                "workflow.request.received",
                {"request_id": req_id, "intent": intent, "request_text": request_text, "source": source or "system", "session_id": active_session_id}
            )

        workflow_id = self.extract_workflow_id(request_text)
        if workflow_id == "FEAT-AUTO":
            workflow_id = self._next_generated_workflow_id()

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
        self._write_workflow_state(state_dir, wf_data, mutation=True)

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
            "next_command": next_skill_info["command"],
            "memory": {
                "status": memory_readiness.status,
                "files_changed": memory_readiness.files_changed,
                "summary_path": ".agents/memory/project-summary.md",
                "context_path": agent_context.context_path,
                "freshness": agent_context.freshness,
                "evidence": list(agent_context.evidence),
                "authority": "current_source_over_memory",
                "provider": agent_context.provider,
                "rag_status": agent_context.rag_status,
                "retrieval_count": len(agent_context.retrieval),
                "memory_action": agent_context.memory_action,
                "memory_receipt": agent_context.memory_receipt,
                "retrieval": list(agent_context.retrieval),
                "next_action": agent_context.next_action,
                "warnings": list(agent_context.warnings),
            },
            "source": source or "system",
            "session_id": active_session_id
        }


__all__ = [
    "AgentContext",
    "MemoryReadiness",
    "WorkflowEntryGateway",
    "build_agent_context",
    "build_context_preflight",
    "ContextPreflightRequest",
    "ensure_project_memory",
]
