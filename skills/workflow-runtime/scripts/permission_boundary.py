# permission_boundary.py
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from event_store import SQLiteEventStore

class PermissionError(Exception):
    pass

class PrivilegeEscalationError(Exception):
    pass

class Permission:
    def __init__(
        self,
        owner_type: str,  # "global" | "session" | "agent" | "tool"
        owner_id: str,
        scope: List[str],  # allowed workspace relative directories (e.g. ["skills", "docs"])
        capabilities: List[str],  # allowed actions (e.g. ["read", "write", "execute"])
        constraints: Optional[Dict[str, Any]] = None,
        duration_seconds: float = 3600.0,
        source: str = "system",
        session_id: str = ""
    ) -> None:
        self.permission_id = str(uuid.uuid4())
        self.owner_type = owner_type
        self.owner_id = owner_id
        self.scope = scope
        self.capabilities = capabilities
        self.constraints = constraints or {}
        self.created_at = datetime.now().astimezone().isoformat()
        self.expires_at = (datetime.now() + timedelta(seconds=duration_seconds)).astimezone().isoformat()
        self.source = source
        self.session_id = session_id or (owner_id if owner_type == "session" else "")
        self.is_revoked = False

    def is_expired(self) -> bool:
        expiry = datetime.fromisoformat(self.expires_at)
        return datetime.now().astimezone() > expiry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permission_id": self.permission_id,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "scope": self.scope,
            "capabilities": self.capabilities,
            "constraints": self.constraints,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "source": self.source,
            "session_id": self.session_id,
            "is_revoked": self.is_revoked
        }

class PermissionBoundary:
    def __init__(self, event_store: Optional[SQLiteEventStore] = None) -> None:
        self.event_store = event_store
        self._permissions: Dict[str, Permission] = {}

    def register_permission(self, perm: Permission) -> None:
        self._permissions[perm.permission_id] = perm
        if self.event_store:
            self.event_store.append_event(
                session_id=perm.session_id,
                topic="permission.created",
                payload=perm.to_dict()
            )

    def revoke_permission(self, permission_id: str) -> None:
        if permission_id in self._permissions:
            perm = self._permissions[permission_id]
            perm.is_revoked = True
            if self.event_store:
                self.event_store.append_event(
                    session_id=perm.session_id,
                    topic="permission.revoked",
                    payload={"permission_id": permission_id}
                )

    def validate_inheritance(self, parent: Permission, child: Permission) -> None:
        # Expiry verification
        if parent.is_expired():
            if self.event_store:
                self.event_store.append_event(
                    session_id=parent.session_id,
                    topic="permission.expired",
                    payload={"permission_id": parent.permission_id}
                )
            raise PermissionError("Parent permission has expired.")
            
        if parent.is_revoked:
            raise PermissionError("Parent permission is revoked.")

        # Child capabilities must be a strict subset of Parent capabilities
        for cap in child.capabilities:
            if cap not in parent.capabilities:
                if self.event_store:
                    self.event_store.append_event(
                        session_id=parent.session_id,
                        topic="permission.violation",
                        payload={"reason": f"privilege escalation: child requests '{cap}'"}
                    )
                raise PrivilegeEscalationError(
                    f"Privilege escalation blocked. Child asks for '{cap}' which parent does not possess."
                )

        # Child scope (directories) must be subset of Parent scope
        for path in child.scope:
            is_subset = False
            for p_path in parent.scope:
                if p_path == "*" or path.startswith(p_path):
                    is_subset = True
                    break
            if not is_subset:
                if self.event_store:
                    self.event_store.append_event(
                        session_id=parent.session_id,
                        topic="permission.violation",
                        payload={"reason": f"scope escalation: path '{path}'"}
                    )
                raise PrivilegeEscalationError(
                    f"Scope escalation blocked. Child scope '{path}' exceeds parent boundary."
                )

        if self.event_store:
            self.event_store.append_event(
                session_id=child.session_id or parent.session_id,
                topic="permission.granted",
                payload=child.to_dict()
            )

    def check_tool_access(self, agent_perm: Permission, command: str, target_path: str) -> None:
        if agent_perm.is_expired() or agent_perm.is_revoked:
            if self.event_store:
                self.event_store.append_event(
                    session_id=agent_perm.session_id,
                    topic="permission.denied",
                    payload={"agent_id": agent_perm.owner_id, "command": command}
                )
            raise PermissionError("Agent permission is invalid, revoked, or expired.")

        # Restrict agent execution permission scope to read-only during brainstorming, planning, and design
        from state_store import get_state_store
        try:
            store = get_state_store()
            workflow = store.get("workflow") or {}
            active_phase = workflow.get("active_phase")
        except Exception:
            active_phase = None

        if active_phase in ["brainstorming", "brainstorm", "planning", "design", "blueprint"]:
            norm_target = os.path.normpath(target_path).replace('\\', '/')
            is_doc_or_scratch = norm_target.startswith("docs/") or norm_target.startswith("scratch/") or norm_target.startswith(".agents/state/")
            is_code_extension = any(norm_target.endswith(ext) for ext in [".py", ".go", ".js", ".ts", ".sh", ".bat", ".ps1"])
            
            if (command in ["write", "execute"] and not is_doc_or_scratch) or is_code_extension:
                if self.event_store:
                    self.event_store.append_event(
                        session_id=agent_perm.session_id,
                        topic="permission.denied",
                        payload={"reason": f"write attempt blocked in read-only phase '{active_phase}'", "target_path": target_path}
                    )
                raise PermissionError(f"Write/execute attempts to code files are blocked during the read-only phase '{active_phase}'.")

        # Tool execute action check
        if "execute" not in agent_perm.capabilities:
            raise PermissionError("Agent permission lacks execute capability.")

        # Cwd scope validation (relative path)
        norm_target = os.path.normpath(target_path)
        is_in_scope = False
        for allowed_path in agent_perm.scope:
            if allowed_path == "*":
                is_in_scope = True
                break
            norm_allowed = os.path.normpath(allowed_path)
            # Check if target is inside allowed path
            if norm_target.startswith(norm_allowed) or norm_target == norm_allowed:
                is_in_scope = True
                break
                
        if not is_in_scope:
            if self.event_store:
                self.event_store.append_event(
                    session_id=agent_perm.session_id,
                    topic="permission.denied",
                    payload={"reason": "scope out of bound", "target_path": target_path}
                )
            raise PermissionError(f"Directory '{target_path}' is out of the allowed agent write scope.")
