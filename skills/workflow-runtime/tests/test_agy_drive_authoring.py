"""Unit tests for the bounded multi-turn AGY authoring drive (no real agy)."""

from __future__ import annotations

from pathlib import Path

from workflow_runtime.application.agent.dispatch_service import AgentDispatchService


class FakeAgy:
    """Records build/execute calls; no subprocess."""

    def __init__(self) -> None:
        self.builds: list[dict[str, object]] = []
        self.executes: int = 0

    def check_binary_available(self) -> bool:
        return True

    def build_command(
        self,
        role_name: str,
        prompt: str,
        model: str,
        effort: str | None,
        timeout_seconds: int,
        add_dir: Path | str | None,
        continue_session: bool = False,
    ) -> list[str]:
        self.builds.append({"prompt": prompt, "continue": continue_session})
        cmd = ["agy"]
        if continue_session:
            cmd.append("--continue")
        cmd.extend(["--mode", "accept-edits", "--print", prompt])
        return cmd

    def execute_dispatch(
        self, command_args: list[str], dry_run: bool, timeout_seconds: int
    ) -> tuple[int, str, str]:
        self.executes += 1
        return (0, "ok", "")


class _StubRole:
    """Placeholder RoleService; drive_authoring never calls it."""


class _StubPrompt:
    """Placeholder PromptService; drive_authoring never calls it."""


def _service(agy: FakeAgy) -> AgentDispatchService:
    return AgentDispatchService(
        role_service=_StubRole(),  # type: ignore[arg-type]
        prompt_service=_StubPrompt(),  # type: ignore[arg-type]
        agy_adapter=agy,  # type: ignore[arg-type]
    )


def test_drive_completes_on_first_turn() -> None:
    agy = FakeAgy()
    result = _service(agy).drive_authoring(
        "blueprint", "TASK", is_complete=lambda: True,
        next_directive=lambda r: f"round {r}", max_rounds=3,
    )
    assert result.completed and result.rounds == 0 and not result.escalated
    assert agy.executes == 1
    assert agy.builds[0]["continue"] is False


def test_drive_continues_until_complete() -> None:
    agy = FakeAgy()
    calls = {"n": 0}

    def is_complete() -> bool:
        calls["n"] += 1
        return calls["n"] >= 3  # incomplete on turns 1,2; complete on 3

    result = _service(agy).drive_authoring(
        "blueprint", "TASK", is_complete=is_complete,
        next_directive=lambda r: f"add remaining phases (round {r})", max_rounds=5,
    )
    assert result.completed and result.rounds == 2 and not result.escalated
    assert agy.executes == 3  # 1 initial + 2 continues
    assert agy.builds[1]["continue"] is True and agy.builds[2]["continue"] is True


def test_drive_escalates_after_max_rounds() -> None:
    agy = FakeAgy()
    result = _service(agy).drive_authoring(
        "blueprint", "TASK", is_complete=lambda: False,
        next_directive=lambda r: f"round {r}", max_rounds=3,
    )
    assert not result.completed and result.escalated and result.rounds == 3
    assert agy.executes == 4  # 1 initial + 3 bounded continues, then stop
    assert "escalate" in result.detail


def test_drive_dry_run_single_turn() -> None:
    agy = FakeAgy()
    result = _service(agy).drive_authoring(
        "blueprint", "TASK", is_complete=lambda: False,
        next_directive=lambda r: "x", dry_run=True, max_rounds=3,
    )
    assert not result.completed and not result.escalated and result.rounds == 0
    assert agy.executes == 1
