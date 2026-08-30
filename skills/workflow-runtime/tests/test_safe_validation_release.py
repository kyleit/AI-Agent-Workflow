from workflow_runtime.application.release.release_gate_service import (
    ReleaseApproval,
    ReleasePlan,
    continue_release_after_approval,
)
from workflow_runtime.application.verification.test_enforcer import (
    authorize_validation,
)
from workflow_runtime.application.security.capability_policy import Capability


def test_autonomous_local_test_is_not_blocked_by_manual_tester_gate() -> None:
    decision = authorize_validation(Capability.LOCAL_TEST, "autonomous")
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_release_approval_is_bound_to_plan_hash() -> None:
    plan = ReleasePlan(version="6.25.1", files=("CHANGELOG.md",), tag="v6.25.1")
    rejected = continue_release_after_approval(plan, ReleaseApproval(plan_hash="stale"))
    accepted = continue_release_after_approval(plan, ReleaseApproval(plan_hash=plan.sha256))
    assert rejected.status == "blocked"
    assert rejected.reason == "approval_plan_hash_mismatch"
    assert accepted.status == "ready"
