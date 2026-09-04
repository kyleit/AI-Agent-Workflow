from __future__ import annotations

from workflow_runtime.application.workflow.lane_scheduler import (
    ExecutionLane,
    FileLeaseStore,
    LaneScheduler,
)
from workflow_runtime.domain.approval import ApprovalRecord, LaneKey, validate_approval
from workflow_runtime.infrastructure.session.lane_state import LaneStateStore


def _lane(agent: str, task: str) -> LaneKey:
    return LaneKey("project-a", "FEAT-608", agent, task)


def _approval(lane: LaneKey, digest: str = "sha-a") -> ApprovalRecord:
    return ApprovalRecord("approval-1", lane, "docs/blueprint.md", digest, "APPROVED", "owner")


def test_approval_requires_exact_lane_and_hash() -> None:
    lane_a = _lane("agent-a", "task-a")
    record = _approval(lane_a)
    assert validate_approval(record, lane_a, "sha-a").approved
    assert validate_approval(record, _lane("agent-b", "task-b"), "sha-a").reason == "LANE_SCOPE_MISMATCH"
    assert validate_approval(record, lane_a, "sha-b").reason == "ARTIFACT_HASH_MISMATCH"


def test_pending_lane_does_not_block_approved_disjoint_lane() -> None:
    lane_a = _lane("agent-a", "task-a")
    lane_b = _lane("agent-b", "task-b")
    scheduler = LaneScheduler(FileLeaseStore())
    decision = scheduler.schedule_lanes([
        ExecutionLane.create(lane_a, ["backend/a.py"], None, "sha-a"),
        ExecutionLane.create(lane_b, ["backend/b.py"], _approval(lane_b), "sha-a"),
    ])
    assert [item.status for item in decision.results] == ["BLOCKED", "RUNNABLE"]
    assert decision.to_dict()["available_lanes"] == [lane_b.value]


def test_same_file_conflict_is_scoped_to_second_lane() -> None:
    lane_a = _lane("agent-a", "task-a")
    lane_b = _lane("agent-b", "task-b")
    scheduler = LaneScheduler(FileLeaseStore())
    first = ExecutionLane.create(lane_a, ["shared.py"], _approval(lane_a), "sha-a")
    second = ExecutionLane.create(lane_b, ["shared.py"], _approval(lane_b), "sha-a")
    decision = scheduler.schedule_lanes([first, second])
    assert [item.status for item in decision.results] == ["RUNNABLE", "BLOCKED"]
    assert decision.results[1].owner_lane == lane_a.value
    scheduler.release(first)


def test_lane_state_isolated_and_atomic(tmp_path) -> None:
    store = LaneStateStore(tmp_path)
    lane_a = _lane("agent-a", "task-a")
    lane_b = _lane("agent-b", "task-b")
    store.save(lane_a, {"status": "running"})
    assert store.load(lane_a) == {"status": "running"}
    assert store.load(lane_b) is None

