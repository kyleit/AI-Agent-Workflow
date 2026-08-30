from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from workflow_runtime.application.command_contract import CommandResult, NextAction


@dataclass(frozen=True)
class WorkflowRequest:
    request_id: str
    work_item_id: str
    action: NextAction
    dispatch: Callable[["WorkflowRequest"], CommandResult]
    history: tuple[str, ...] = field(default_factory=tuple)

    def idempotency_key(self, action: NextAction) -> str:
        args = tuple(sorted((str(key), str(value)) for key, value in action.arguments.items()))
        return f"{self.work_item_id}:{action.skill or ''}:{action.command or ''}:{args}"

    def follow(self, action: NextAction) -> "WorkflowRequest":
        return WorkflowRequest(
            self.request_id,
            self.work_item_id,
            action,
            self.dispatch,
            self.history + (self.idempotency_key(action),),
        )


@dataclass(frozen=True)
class WorkflowResult:
    status: str
    results: tuple[CommandResult, ...]
    reason: str = ""
    next_action: NextAction | None = None

    @classmethod
    def completed_or_waiting(cls, results: list[CommandResult]) -> "WorkflowResult":
        last = results[-1] if results else None
        action = last.next_action if last and last.next_action.command else None
        status = "waiting_approval" if action and action.requires_approval else "completed"
        return cls(status, tuple(results), next_action=action)

    @classmethod
    def blocked(cls, results: list[CommandResult], reason: str) -> "WorkflowResult":
        return cls("blocked", tuple(results), reason=reason)


def execute_until_stop(request: WorkflowRequest, budget: int = 32) -> WorkflowResult:
    seen: set[str] = set(request.history)
    results: list[CommandResult] = []
    current = request
    for _ in range(max(1, budget)):
        result = current.dispatch(current)
        results.append(result)
        action = result.next_action
        if not action.command or not action.automatic:
            return WorkflowResult.completed_or_waiting(results)
        key = current.idempotency_key(action)
        if key in seen:
            return WorkflowResult.blocked(results, "continuation_cycle_detected")
        seen.add(key)
        current = current.follow(action)
    return WorkflowResult.blocked(results, "continuation_budget_exhausted")


__all__ = ["WorkflowRequest", "WorkflowResult", "execute_until_stop"]
