"""Injected application use cases; no filesystem or environment access."""
from __future__ import annotations

from collections.abc import Sequence

from .domain import ActorContext, DecisionReason, PathDecision, evaluate_path
from .ports import BatchDecision, CapabilityRepository, IssueRequest, IssueResult, SourceChange


def authorize_paths(changes: Sequence[SourceChange], actor: ActorContext,
                    repository: CapabilityRepository, now: int) -> BatchDecision:
    snapshot = repository.load_snapshot(actor.work_item_id)
    decisions: list[PathDecision] = []
    for change in changes:
        endpoints = [change.path] + ([change.old_path] if change.old_path else [])
        pair = [evaluate_path(path, change.operation, actor, snapshot, now)
                if repository.contains(path) else
                PathDecision(False, DecisionReason.SCOPE_INVALID, path.value, change.operation, actor.work_item_id)
                for path in endpoints]
        if len(pair) == 2 and all(d.allowed for d in pair) and pair[0].work_item_id != pair[1].work_item_id:
            pair = [PathDecision(False, DecisionReason.CONTEXT_MISMATCH, d.path, d.operation, d.work_item_id)
                    for d in pair]
        decisions.extend(pair)
    return BatchDecision(all(d.allowed for d in decisions), tuple(decisions))


def issue_capability(request: IssueRequest, repository: CapabilityRepository) -> IssueResult:
    return repository.publish(request)
