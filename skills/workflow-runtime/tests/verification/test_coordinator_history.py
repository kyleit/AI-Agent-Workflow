from __future__ import annotations

import json
import time
from pathlib import Path

from workflow_runtime.application.verification.test_coordinator import (
    TestCoordinator as Coordinator,
    normalize_pytest_history,
)


def test_normalize_legacy_scalar_and_malformed_history() -> None:
    now = time.time()
    valid, invalid = normalize_pytest_history(
        [now - 1, {"timestamp": now - 2}, None, "bad", {"missing": True}, True],
        now,
    )
    assert len(valid) == 2
    assert invalid == 4


def test_rate_limit_ignores_legacy_scalar_records(tmp_path: Path) -> None:
    state_dir = tmp_path / ".agents" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "pytest_history.json").write_text(
        json.dumps([time.time() - 1, {"timestamp": time.time() - 2}, None]),
        encoding="utf-8",
    )
    ok, reason = Coordinator(str(tmp_path)).check_rate_limit()
    assert ok is True
    assert "malformed" in reason
