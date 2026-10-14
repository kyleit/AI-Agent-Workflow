"""Throwaway CONTRACT spike: typed values and pure per-path decision rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SourceOperation(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class CapabilityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class DecisionReason(str, Enum):
    ALLOW = "ALLOW"
    SCOPE_INVALID = "SCOPE_INVALID"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    CAPABILITY_INVALID = "CAPABILITY_INVALID"
    CAPABILITY_INACTIVE = "CAPABILITY_INACTIVE"
    APPROVAL_MISMATCH = "APPROVAL_MISMATCH"
    SNAPSHOT_CHANGED = "SNAPSHOT_CHANGED"
    SCOPE_CONFLICT = "SCOPE_CONFLICT"
    SCOPE_UNOWNED = "SCOPE_UNOWNED"


@dataclass(frozen=True)
class RepoPath:
    value: str
    windows: bool = False

    def __post_init__(self) -> None:
        normalized = self.value.replace("\\", "/")
        if (
            not normalized
            or normalized.startswith("/")
            or ":" in normalized
            or "\0" in normalized
            or any(char in normalized for char in "*?[]")
            or any(part in {"", ".", ".."} for part in normalized.split("/"))
        ):
            raise ValueError(DecisionReason.SCOPE_INVALID.value)
        object.__setattr__(self, "value", normalized)

    @property
    def key(self) -> str:
        return self.value.casefold() if self.windows else self.value


@dataclass(frozen=True)
class ActorContext:
    project_id: str
    work_item_id: str | None = None
    owner_id: str | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class Capability:
    work_item_id: str
    project_id: str
    status: CapabilityStatus
    phase: str
    scope: tuple[RepoPath, ...]
    owner_id: str
    session_id: str
    issued_at: int
    expires_at: int
    bindings_valid: bool
    snapshot_consistent: bool = True

    def __post_init__(self) -> None:
        if not re.fullmatch(r"(?:FEAT|FIX|QUICK)-[0-9]+", self.work_item_id):
            raise ValueError(DecisionReason.CAPABILITY_INVALID.value)
        if not self.project_id or not self.owner_id or not self.session_id:
            raise ValueError(DecisionReason.CAPABILITY_INVALID.value)
        if not self.scope or len({path.key for path in self.scope}) != len(self.scope):
            raise ValueError(DecisionReason.SCOPE_INVALID.value)
        if type(self.issued_at) is not int or type(self.expires_at) is not int:
            raise ValueError(DecisionReason.CAPABILITY_INVALID.value)
        if self.expires_at <= self.issued_at:
            raise ValueError(DecisionReason.CAPABILITY_INVALID.value)


@dataclass(frozen=True)
class CapabilitySnapshot:
    records: tuple[Capability, ...]

    def __post_init__(self) -> None:
        identities = {record.work_item_id for record in self.records}
        if len(identities) != len(self.records):
            raise ValueError(DecisionReason.CAPABILITY_INVALID.value)


@dataclass(frozen=True)
class PathDecision:
    allowed: bool
    reason: DecisionReason
    path: str
    operation: SourceOperation
    work_item_id: str | None
    conflicting_work_items: tuple[str, ...] = ()


IMPLEMENTATION_PHASES = frozenset({"implementation", "debug", "verification"})


def _eligibility(record: Capability, actor: ActorContext, now: int) -> DecisionReason:
    if record.project_id != actor.project_id:
        return DecisionReason.CONTEXT_MISMATCH
    if not record.snapshot_consistent:
        return DecisionReason.SNAPSHOT_CHANGED
    if record.status is not CapabilityStatus.ACTIVE:
        return DecisionReason.CAPABILITY_INACTIVE
    if record.issued_at > now or record.expires_at <= now:
        return DecisionReason.CAPABILITY_INACTIVE
    if record.phase not in IMPLEMENTATION_PHASES or not record.bindings_valid:
        return DecisionReason.APPROVAL_MISMATCH
    return DecisionReason.ALLOW


def evaluate_path(
    path: RepoPath,
    operation: SourceOperation,
    actor: ActorContext,
    snapshot: CapabilitySnapshot,
    now: int,
) -> PathDecision:
    """C02 validates actual artifacts; this rule consumes its immutable proof."""
    selected: Capability | None = None
    if actor.work_item_id is not None:
        selected = next(
            (record for record in snapshot.records if record.work_item_id == actor.work_item_id),
            None,
        )
        if selected is None:
            return PathDecision(False, DecisionReason.CAPABILITY_INVALID, path.value, operation, actor.work_item_id)
        reason = _eligibility(selected, actor, now)
        if reason is not DecisionReason.ALLOW:
            return PathDecision(False, reason, path.value, operation, actor.work_item_id)
        if not any(owned.key == path.key for owned in selected.scope):
            return PathDecision(False, DecisionReason.SCOPE_UNOWNED, path.value, operation, actor.work_item_id)

    claimants = tuple(
        record for record in snapshot.records
        if _eligibility(record, actor, now) is DecisionReason.ALLOW
        and any(owned.key == path.key for owned in record.scope)
    )
    if len(claimants) > 1:
        owners = tuple(sorted(record.work_item_id for record in claimants))
        return PathDecision(False, DecisionReason.SCOPE_CONFLICT, path.value, operation, actor.work_item_id, owners)
    if not claimants:
        return PathDecision(False, DecisionReason.SCOPE_UNOWNED, path.value, operation, actor.work_item_id)
    owner = claimants[0]
    if (
        (actor.owner_id is not None and actor.owner_id != owner.owner_id)
        or (actor.session_id is not None and actor.session_id != owner.session_id)
    ):
        return PathDecision(False, DecisionReason.CONTEXT_MISMATCH, path.value, operation, actor.work_item_id)
    return PathDecision(True, DecisionReason.ALLOW, path.value, operation, owner.work_item_id)
