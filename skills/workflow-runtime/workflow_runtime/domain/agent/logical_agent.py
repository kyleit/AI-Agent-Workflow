from __future__ import annotations

from datetime import datetime
from typing import Any

from workflow_runtime.domain.ports.event_store_port import EventStorePort


class AgentTransitionError(Exception):
    pass


class LogicalAgent:
    def __init__(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        capabilities: list[str],
        permissions: str = "sandbox",
        retry_policy: dict[str, Any] | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.session_id = session_id
        self.role = role
        self.capabilities = capabilities
        self.permissions = permissions
        self.retry_policy: dict[str, Any] = retry_policy or {"max_retries": 3, "backoff_factor": 2.0}

        self.goal: str = ""
        self.assigned_tasks: list[Any] = []
        self.status: str = "declared"
        self.priority: str = "medium"
        self.dependencies: list[Any] = []
        self.retry_count: int = 0
        self.cancellation_state: str = "active"

        self.context_delta: dict[str, Any] = {
            "scratch_context": {},
            "local_decisions": [],
            "evidence_references": [],
            "output_summary": ""
        }
        self.input_refs: list[Any] = []
        self.output_refs: list[Any] = []

        self.created_at: str = datetime.now().astimezone().isoformat()
        self.updated_at: str = self.created_at

    def to_dict(self) -> dict[str, Any]:
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

    def transition_to(self, target_status: str, event_store: EventStorePort | None = None) -> None:
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
                aggregate_id=self.session_id,
                event_type=topic,
                payload={"agent_id": self.agent_id, "status": self.status}
            )

    def cancel(self, reason: str = "cancelled", event_store: EventStorePort | None = None) -> None:
        if self.cancellation_state == "cancelled":
            return

        self.cancellation_state = "cancelled"
        try:
            self.transition_to("cancelled", event_store)
        except AgentTransitionError:
            self.status = "cancelled"
            if event_store:
                event_store.append_event(
                    aggregate_id=self.session_id,
                    event_type="agent.cancelled",
                    payload={"agent_id": self.agent_id, "status": "cancelled", "reason": reason}
                )

    def trigger_retry(self, reason: str, event_store: EventStorePort | None = None) -> bool:
        max_retries = int(str(self.retry_policy.get("max_retries", 3)))
        if self.retry_count >= max_retries:
            self.transition_to("failed", event_store)
            return False

        self.retry_count += 1
        self.transition_to("retrying", event_store)
        self.transition_to("ready", event_store)
        return True


__all__ = [
    "AgentTransitionError",
    "LogicalAgent",
]
