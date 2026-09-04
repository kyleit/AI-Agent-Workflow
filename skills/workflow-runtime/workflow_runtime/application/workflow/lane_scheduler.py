from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

from workflow_runtime.domain.approval import ApprovalRecord, LaneKey, validate_approval


@dataclass(frozen=True)
class ExecutionLane:
    lane: LaneKey
    write_set: tuple[str, ...] = ()
    approval: ApprovalRecord | None = None
    artifact_sha256: str = ""

    @classmethod
    def create(
        cls,
        lane: LaneKey,
        write_set: Iterable[str],
        approval: ApprovalRecord | None,
        artifact_sha256: str,
    ) -> "ExecutionLane":
        return cls(lane, tuple(sorted(set(str(path) for path in write_set))), approval, artifact_sha256)


@dataclass(frozen=True)
class LaneResult:
    lane: LaneKey
    status: str
    evidence: tuple[str, ...] = ()
    owner_lane: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "lane": self.lane.to_dict(),
            "status": self.status,
            "evidence": list(self.evidence),
        }
        if self.owner_lane:
            result["owner_lane"] = self.owner_lane
        return result


@dataclass(frozen=True)
class ScheduleDecision:
    results: tuple[LaneResult, ...]

    @property
    def runnable(self) -> tuple[LaneResult, ...]:
        return tuple(item for item in self.results if item.status == "RUNNABLE")

    @property
    def blocked(self) -> tuple[LaneResult, ...]:
        return tuple(item for item in self.results if item.status == "BLOCKED")

    def to_dict(self) -> dict[str, Any]:
        blocked = self.blocked
        return {
            "status": "blocked" if blocked and not self.runnable else "ready",
            "results": [item.to_dict() for item in self.results],
            "blocked_scope": [item.lane.to_dict() for item in blocked],
            "available_lanes": [item.lane.value for item in self.runnable],
            "evidence": [evidence for item in self.results for evidence in item.evidence],
            "next_action": (
                f"continue available lane {self.runnable[0].lane.value}"
                if self.runnable else "resolve lane-scoped blockers"
            ),
        }


@dataclass
class _Lease:
    lane_value: str
    expires_at: float


class FileLeaseStore:
    """Small process-local lease store; durable state is owned by the lane state adapter."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._leases: dict[str, _Lease] = {}
        self._lock = threading.Lock()

    def acquire(self, lane: LaneKey, paths: Iterable[str], now: float | None = None) -> str | None:
        timestamp = now if now is not None else time.time()
        normalized = sorted(set(str(path) for path in paths))
        with self._lock:
            for path in normalized:
                lease = self._leases.get(path)
                if lease and lease.expires_at > timestamp and lease.lane_value != lane.value:
                    return lease.lane_value
            for path in normalized:
                self._leases[path] = _Lease(lane.value, timestamp + self.ttl_seconds)
        return None

    def release(self, lane: LaneKey) -> None:
        with self._lock:
            self._leases = {path: lease for path, lease in self._leases.items() if lease.lane_value != lane.value}


class LaneScheduler:
    def __init__(self, leases: FileLeaseStore | None = None) -> None:
        self.leases = leases or FileLeaseStore()

    def schedule_lanes(self, lanes: Iterable[ExecutionLane]) -> ScheduleDecision:
        results: list[LaneResult] = []
        for lane in lanes:
            if lane.approval is None:
                results.append(LaneResult(lane.lane, "BLOCKED", ("APPROVAL_PENDING",)))
                continue
            approval = validate_approval(lane.approval, lane.lane, lane.artifact_sha256)
            if not approval.approved:
                results.append(LaneResult(lane.lane, "BLOCKED", (approval.reason,)))
                continue
            owner = self.leases.acquire(lane.lane, lane.write_set)
            if owner:
                results.append(LaneResult(lane.lane, "BLOCKED", ("FILE_LEASE_CONFLICT",), owner))
                continue
            results.append(LaneResult(lane.lane, "RUNNABLE", ("APPROVAL_VALID",)))
        return ScheduleDecision(tuple(results))

    def release(self, lane: ExecutionLane | LaneKey) -> None:
        self.leases.release(lane.lane if isinstance(lane, ExecutionLane) else lane)


def schedule_lanes(lanes: Iterable[ExecutionLane]) -> ScheduleDecision:
    return LaneScheduler().schedule_lanes(lanes)


__all__ = ["ExecutionLane", "FileLeaseStore", "LaneResult", "LaneScheduler", "ScheduleDecision", "schedule_lanes"]

