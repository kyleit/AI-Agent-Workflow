# logical_agent.py
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from event_store import SQLiteEventStore

class AgentTransitionError(Exception):
    pass

class LogicalAgent:
    def __init__(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        capabilities: List[str],
        permissions: str = "sandbox",
        retry_policy: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.agent_id = agent_id
        self.session_id = session_id
        self.role = role
        self.capabilities = capabilities
        self.permissions = permissions
        self.retry_policy = retry_policy or {"max_retries": 3, "backoff_factor": 2.0}
        
        # Core state fields
        self.goal = ""
        self.assigned_tasks = []
        self.status = "declared"
        self.priority = "medium"
        self.dependencies = []
        self.retry_count = 0
        self.cancellation_state = "active"  # "active" | "cancelled"
        
        # Scoped memory structures
        self.context_delta = {
            "scratch_context": {},
            "local_decisions": [],
            "evidence_references": [],
            "output_summary": ""
        }
        self.input_refs = []
        self.output_refs = []
        
        self.created_at = datetime.now().astimezone().isoformat()
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "role": self.role,
            "capabilities": self.capabilities,
            "permissions": self.permissions,
            "retry_policy": self.retry_policy,
            "goal": self.goal,
            "assigned_tasks": self.assigned_tasks,
            "status": self.status,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "cancellation_state": self.cancellation_state,
            "context_delta": self.context_delta,
            "input_refs": self.input_refs,
            "output_refs": self.output_refs,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def transition_to(self, target_status: str, event_store: Optional[SQLiteEventStore] = None) -> None:
        VALID_TRANSITIONS = {
            "declared": ["ready", "cancelled", "failed"],
            "ready": ["scheduled", "cancelled", "failed"],
            "scheduled": ["executing", "cancelled", "failed"],
            "executing": ["waiting", "completed", "failed", "cancelled", "retrying", "blocked"],
            "waiting": ["executing", "cancelled", "failed"],
            "blocked": ["ready", "cancelled", "failed"],
            "retrying": ["ready", "cancelled", "failed"],
            "completed": [],
            "failed": [],
            "cancelled": []
        }
        
        current = self.status
        allowed = VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise AgentTransitionError(f"Illegal agent transition from '{current}' to '{target_status}'")
            
        self.status = target_status
        self.updated_at = datetime.now().astimezone().isoformat()
        
        if event_store:
            topic = f"agent.{target_status}"
            event_store.append_event(
                session_id=self.session_id,
                topic=topic,
                payload={"agent_id": self.agent_id, "status": self.status}
            )

    def cancel(self, reason: str = "cancelled", event_store: Optional[SQLiteEventStore] = None) -> None:
        if self.cancellation_state == "cancelled":
            return  # Idempotent check
            
        self.cancellation_state = "cancelled"
        try:
            self.transition_to("cancelled", event_store)
        except AgentTransitionError:
            # Force transition if in terminal state
            self.status = "cancelled"
            if event_store:
                event_store.append_event(
                    session_id=self.session_id,
                    topic="agent.cancelled",
                    payload={"agent_id": self.agent_id, "status": "cancelled", "reason": reason}
                )

    def trigger_retry(self, reason: str, event_store: Optional[SQLiteEventStore] = None) -> bool:
        max_retries = self.retry_policy.get("max_retries", 3)
        if self.retry_count >= max_retries:
            self.transition_to("failed", event_store)
            return False  # Max retries reached
            
        self.retry_count += 1
        self.transition_to("retrying", event_store)
        self.transition_to("ready", event_store)
        return True
