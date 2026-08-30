from workflow_runtime.application.command_contract import CommandResult, NextAction
from workflow_runtime.application.workflow.supervisor_loop import (
    WorkflowRequest,
    execute_until_stop,
)
from workflow_runtime.presentation.cli.commands._impl.session import session_lifecycle


def test_supervisor_follows_automatic_actions_until_completion() -> None:
    calls: list[str] = []

    def dispatch(request: WorkflowRequest) -> CommandResult:
        calls.append(request.action.command or "")
        if len(calls) == 1:
            return CommandResult(
                command="step-one",
                status="success",
                summary="first",
                next_action=NextAction(command="step-two", automatic=True),
            )
        return CommandResult(command="step-two", status="success", summary="done")

    result = execute_until_stop(WorkflowRequest("REQ-1", "FEAT-061", NextAction(command="step-one"), dispatch), budget=4)
    assert result.status == "completed"
    assert calls == ["step-one", "step-two"]


def test_supervisor_stops_on_continuation_cycle() -> None:
    def dispatch(_request: WorkflowRequest) -> CommandResult:
        return CommandResult(
            command="loop",
            status="success",
            summary="loop",
            next_action=NextAction(command="loop", automatic=True),
        )

    result = execute_until_stop(WorkflowRequest("REQ-2", "FEAT-061", NextAction(command="loop"), dispatch), budget=4)
    assert result.status == "blocked"
    assert result.reason == "continuation_cycle_detected"


def test_supervisor_preserves_approval_boundary() -> None:
    def dispatch(_request: WorkflowRequest) -> CommandResult:
        return CommandResult(
            command="prepare",
            status="success",
            summary="needs approval",
            next_action=NextAction(command="release", automatic=False, requires_approval=True),
        )

    result = execute_until_stop(WorkflowRequest("REQ-3", "FEAT-061", NextAction(command="prepare"), dispatch), budget=4)
    assert result.status == "waiting_approval"
    assert result.next_action is not None
    assert result.next_action.requires_approval is True


def test_start_implementation_synchronizes_active_phase(monkeypatch) -> None:
    saved: list[dict[str, object]] = []
    session = {
        "work_item": {"id": "FEAT-061"},
        "blueprint": {"path": "docs/FEAT-061_blueprint.md", "approved": True, "work_item_id": "FEAT-061"},
        "checkpoint": 1,
    }
    monkeypatch.setattr(session_lifecycle.WorkflowLease, "acquire", staticmethod(lambda *_args: True))
    monkeypatch.setattr(session_lifecycle, "update_context_health", lambda _session: None)
    monkeypatch.setattr(session_lifecycle, "load_session", lambda: dict(session))
    monkeypatch.setattr(session_lifecycle, "save_session_atomic", lambda value: saved.append(dict(value)))

    args = type(
        "Args",
        (),
        {
            "skill": "blueprint-to-implementation",
            "command": "implement",
            "checkpoint": 6,
            "step": "implementation entry",
            "autonomous": True,
            "blueprint": "",
        },
    )()
    session_lifecycle.do_start(args)
    assert saved[-1]["active_phase"] == "implementation"
    assert saved[-1]["suggested_next_skill"] == "blueprint-to-implementation"
    assert saved[-1]["suggested_next_command"] == "implement"


def test_legacy_approval_for_other_work_item_is_not_migrated(tmp_path, monkeypatch) -> None:
    from workflow_runtime.infrastructure.session.state_store import AtomicFileStateStore

    state_root = tmp_path / "state"
    state_root.mkdir()
    (state_root / "workflow.json").write_text(
        '{"active_workflow":"FEAT-061"}', encoding="utf-8",
    )
    (state_root / "approvals.json").write_text(
        '{"blueprint":{"path":"docs/FIX-029_blueprint.md","approved":true,"work_item":"FIX-029"}}',
        encoding="utf-8",
    )
    monkeypatch.setenv("AIWF_STATE_ROOT", str(state_root))
    store = AtomicFileStateStore(str(state_root))
    assert store.get("approvals") == {}
    assert not (state_root / "work-items" / "FEAT-061" / "approvals.json").exists()
