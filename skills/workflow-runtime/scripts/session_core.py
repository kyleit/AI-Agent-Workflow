# session_core.py
import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from event_store import SQLiteEventStore

class SessionInitError(Exception):
    pass

class SessionNotFoundError(Exception):
    pass

class SessionRuntimeCore:
    def __init__(
        self,
        session_id: str,
        workspace_path: str = ".",
        permission_mode: str = "sandbox",
        token_budget: int = 500000,
    ) -> None:
        self.session_id = session_id
        self.workspace_path = workspace_path
        self.permission_mode = permission_mode
        self.token_budget = token_budget
        self.status = "created"
        self.created_at = datetime.now().astimezone().isoformat()
        self.updated_at = self.created_at
        self.active_work_item_id = "N/A"
        self.memory_baseline_rss = 0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "workspace_path": self.workspace_path,
            "permission_mode": self.permission_mode,
            "token_budget": self.token_budget,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active_work_item_id": self.active_work_item_id,
            "memory_baseline_rss": self.memory_baseline_rss,
        }

    def transition_to(self, target_status: str) -> None:
        VALID_TRANSITIONS = {
            "created": ["initializing", "cancelled", "failed"],
            "initializing": ["planning", "cancelled", "failed"],
            "planning": ["ready", "cancelled", "failed"],
            "ready": ["running", "cancelled", "failed"],
            "running": ["waiting_for_tool", "integrating", "verifying", "cancelled", "failed"],
            "waiting_for_tool": ["running", "cancelled", "failed"],
            "integrating": ["verifying", "cancelled", "failed"],
            "verifying": ["final_review", "completed", "failed", "cancelled"],
            "final_review": ["completed", "failed", "cancelled"],
            "completed": [],
            "failed": [],
            "cancelled": []
        }
        
        current = self.status
        allowed = VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise ValueError(f"Illegal state transition from '{current}' to '{target_status}'")
            
        self.status = target_status
        self.updated_at = datetime.now().astimezone().isoformat()

def create_session(request_id: str, work_item: str, permission_mode: str = "sandbox") -> SessionRuntimeCore:
    if not os.path.exists(".agents"):
        raise SessionInitError("Workspace is not initialized. Missing '.agents' directory.")
        
    session_id = str(uuid.uuid4())
    session = SessionRuntimeCore(session_id=session_id, permission_mode=permission_mode)
    session.active_work_item_id = work_item
    session.transition_to("initializing")
    return session

def checkpoint_session(session: SessionRuntimeCore, event_store: SQLiteEventStore) -> None:
    # Save a snapshot event into WAL event store
    event_store.append_event(
        session_id=session.session_id,
        topic="session.checkpoint",
        payload=session.to_dict()
    )
    
    # Atomic write to context.json for backward compatibility
    state_dir = os.path.join(session.workspace_path, ".agents", "state")
    os.makedirs(state_dir, exist_ok=True)
    context_path = os.path.join(state_dir, "context.json")
    
    # Read existing context or start fresh
    existing = {}
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
            
    existing.update({
        "session_id": session.session_id,
        "permission_mode": session.permission_mode,
        "checkpoint_status": session.status,
        "active_work_item": session.active_work_item_id,
        "updated_at": session.updated_at
    })
    
    temp_path = context_path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    os.replace(temp_path, context_path)

def recover_session(session_id: str, event_store: SQLiteEventStore) -> SessionRuntimeCore:
    events = event_store.get_events(session_id)
    if not events:
        raise SessionNotFoundError(f"No events found for session: {session_id}")
        
    session = SessionRuntimeCore(session_id=session_id)
    for event in events:
        topic = event["topic"]
        payload = event["payload"]
        
        if topic == "session.checkpoint":
            session.workspace_path = payload.get("workspace_path", ".")
            session.permission_mode = payload.get("permission_mode", "sandbox")
            session.token_budget = payload.get("token_budget", 500000)
            session.status = payload.get("status", "created")
            session.created_at = payload.get("created_at", session.created_at)
            session.updated_at = payload.get("updated_at", session.updated_at)
            session.active_work_item_id = payload.get("active_work_item_id", "N/A")
            session.memory_baseline_rss = payload.get("memory_baseline_rss", 0)
            
    return session
