"""Checkpoint ordering must not block the default gate-free workflow."""
from __future__ import annotations

import argparse
import json

import pytest

from workflow_runtime.presentation.cli.commands._impl.system import system_health


@pytest.mark.parametrize("session", [None, {"checkpoint": 1},
    {"checkpoint": 1, "context_health": "broken"}])
@pytest.mark.parametrize("mode", [None, "off"])
def test_checkpoint_gate_skips_without_changing_state(
    session, mode, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    if mode is None:
        monkeypatch.delenv("AIWF_GATE_MODE", raising=False)
    else:
        monkeypatch.setenv("AIWF_GATE_MODE", mode)
    original = dict(session) if session else session
    monkeypatch.setattr(system_health, "load_session", lambda: session)

    def unexpected_write(*_args) -> None:
        pytest.fail("A skipped checkpoint check must not repair or rewrite session state")

    monkeypatch.setattr(system_health, "save_session_atomic", unexpected_write)
    monkeypatch.setattr(system_health, "update_context_health", unexpected_write)
    assert system_health.do_validate(argparse.Namespace(checkpoint="exactly 2")) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["gate_status"] == "SKIPPED"
    assert result["current_checkpoint"] == (1 if session else None)
    assert result["required_checkpoint"] == "exactly 2"
    assert session == original


def test_checkpoint_gate_blocks_only_with_explicit_enforcement(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AIWF_GATE_MODE", "enforce")
    monkeypatch.setattr(system_health, "load_session", lambda: {"checkpoint": 1})
    monkeypatch.setattr(system_health, "update_context_health", lambda _session: None)
    with pytest.raises(SystemExit) as error:
        system_health.do_validate(argparse.Namespace(checkpoint="exactly 2"))
    assert error.value.code == 1
    assert "current=1, required=exactly 2" in capsys.readouterr().err


def test_explicit_session_diagnostics_still_report_missing_session(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("AIWF_GATE_MODE", raising=False)
    monkeypatch.setattr(system_health, "load_session", lambda: None)
    with pytest.raises(SystemExit) as error:
        system_health.do_validate(argparse.Namespace(subaction="session"))
    assert error.value.code == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failure"
