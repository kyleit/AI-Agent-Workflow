from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workflow_runtime.application.workflow.phase_controller import (
    CompletionGateBlocked,
    PhaseController,
)

pytestmark = pytest.mark.e2e


class _CompletedLedger:
    def mark_phase_completed(self, phase_id: str) -> None:
        del phase_id

    def get_next_incomplete_phase(self) -> None:
        return None

    def is_feature_complete(self) -> bool:
        return True


def _profile(root, required: bool) -> None:
    agents = root / ".agents"
    agents.mkdir()
    (agents / "project-profile.json").write_text(
        json.dumps({"visual_debug": {"e2e_required": required}}), encoding="utf-8"
    )


def test_frontend_completion_is_blocked_without_visual_pass(tmp_path):
    _profile(tmp_path, True)
    controller = PhaseController(workspace_root=str(tmp_path))
    controller._ledger = _CompletedLedger()

    with pytest.raises(CompletionGateBlocked) as error:
        controller.on_phase_completed("phase-1")

    assert error.value.code == "FRONTEND_E2E_REQUIRED"


def test_non_frontend_completion_keeps_existing_transition(tmp_path):
    _profile(tmp_path, False)
    controller = PhaseController(workspace_root=str(tmp_path))
    controller._ledger = _CompletedLedger()

    result = controller.on_phase_completed("phase-1")

    assert result["next_action"] == "debug"
