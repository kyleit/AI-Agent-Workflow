from workflow_runtime.application.security.capability_policy import (
    Capability,
    decide_capability,
)


def test_autonomous_mode_allows_safe_local_validation() -> None:
    for capability in (Capability.READ, Capability.COMPILE, Capability.LINT, Capability.LOCAL_TEST):
        decision = decide_capability("autonomous", capability, blueprint_approved=False)
        assert decision.allowed is True
        assert decision.requires_approval is False


def test_autonomous_local_write_requires_approved_blueprint() -> None:
    denied = decide_capability("autonomous", Capability.LOCAL_WRITE, blueprint_approved=False)
    allowed = decide_capability("autonomous", Capability.LOCAL_WRITE, blueprint_approved=True)
    assert denied.allowed is False
    assert denied.requires_approval is True
    assert allowed.allowed is True


def test_risky_capabilities_pause_for_specific_approval() -> None:
    for capability in (Capability.NETWORK, Capability.DESTRUCTIVE, Capability.RELEASE, Capability.PRODUCTION):
        decision = decide_capability("autonomous", capability, blueprint_approved=True)
        assert decision.allowed is False
        assert decision.requires_approval is True


def test_legacy_mode_keeps_state_changing_prompt() -> None:
    decision = decide_capability("legacy", Capability.LOCAL_WRITE, blueprint_approved=True)
    assert decision.allowed is False
    assert decision.requires_approval is True
