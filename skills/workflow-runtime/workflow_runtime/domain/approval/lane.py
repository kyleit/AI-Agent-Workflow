from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


def _required(value: str, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


@dataclass(frozen=True)
class LaneKey:
    """Stable identity for one Agent's work inside one project workflow."""

    project_id: str
    workflow_id: str
    agent_id: str
    task_id: str

    def __post_init__(self) -> None:
        for field in ("project_id", "workflow_id", "agent_id", "task_id"):
            _required(getattr(self, field), field)

    @property
    def value(self) -> str:
        return "/".join((self.project_id, self.workflow_id, self.agent_id, self.task_id))

    def to_dict(self) -> dict[str, str]:
        return {
            "project_id": self.project_id,
            "workflow_id": self.workflow_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "LaneKey":
        return cls(
            project_id=_required(str(value.get("project_id", "")), "project_id"),
            workflow_id=_required(str(value.get("workflow_id", "")), "workflow_id"),
            agent_id=_required(str(value.get("agent_id", "")), "agent_id"),
            task_id=_required(str(value.get("task_id", "")), "task_id"),
        )


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"approved": self.approved, "reason": self.reason}


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    lane: LaneKey
    artifact_path: str
    artifact_sha256: str
    status: str = "PENDING"
    approved_by: str = ""
    expires_at: str | None = None

    def __post_init__(self) -> None:
        _required(self.approval_id, "approval_id")
        _required(self.artifact_path, "artifact_path")
        _required(self.artifact_sha256, "artifact_sha256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            **self.lane.to_dict(),
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "status": self.status,
            "approved_by": self.approved_by,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ApprovalRecord":
        return cls(
            approval_id=_required(str(value.get("approval_id", "")), "approval_id"),
            lane=LaneKey.from_dict(value),
            artifact_path=_required(str(value.get("artifact_path", "")), "artifact_path"),
            artifact_sha256=_required(str(value.get("artifact_sha256", "")), "artifact_sha256"),
            status=str(value.get("status", "PENDING")),
            approved_by=str(value.get("approved_by", "")),
            expires_at=str(value["expires_at"]) if value.get("expires_at") else None,
        )


def _expired(expires_at: str | None, now: datetime) -> bool:
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry <= now
    except ValueError:
        return True


def validate_approval(
    record: ApprovalRecord,
    lane: LaneKey,
    artifact_sha256: str,
    now: datetime | None = None,
) -> ApprovalDecision:
    """Accept only an approved record with an exact lane and artifact hash."""
    if record.lane != lane:
        return ApprovalDecision(False, "LANE_SCOPE_MISMATCH")
    if record.artifact_sha256 != artifact_sha256:
        return ApprovalDecision(False, "ARTIFACT_HASH_MISMATCH")
    if str(record.status).upper() != "APPROVED":
        return ApprovalDecision(False, "APPROVAL_NOT_APPROVED")
    if _expired(record.expires_at, now or datetime.now(timezone.utc)):
        return ApprovalDecision(False, "APPROVAL_EXPIRED")
    return ApprovalDecision(True, "APPROVED")

