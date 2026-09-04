from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from workflow_runtime.application.workflow.blueprint_lifecycle import BlueprintLifecycleService


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / "src").mkdir()
    (tmp_path / "docs" / "features").mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    blueprint = tmp_path / "docs" / "features" / "FEAT-TEST.md"
    blueprint.write_text(
        "---\ncreated_at: 2026-09-01T00:00:00+00:00\n---\n\n# Blueprint\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=aiwf@example.invalid", "-c", "user.name=AIWF", "commit", "-qm", "initial"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path, blueprint


def test_blueprint_lifecycle_records_current_snapshot_and_detects_source_drift(tmp_path: Path) -> None:
    root, blueprint = _repo(tmp_path)
    service = BlueprintLifecycleService(root=root, max_age_days=30)

    current = service.inspect(blueprint, "FEAT-TEST", datetime(2026, 9, 4, tzinfo=timezone.utc))
    assert current.lifecycle_state == "PENDING"
    assert current.stale is False
    assert (root / current.registry_path).is_file()

    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    drifted = service.inspect(blueprint, "FEAT-TEST", datetime(2026, 9, 4, tzinfo=timezone.utc))
    assert drifted.lifecycle_state == "STALE"
    assert "blueprint_source_drift" in drifted.reasons


def test_blueprint_lifecycle_detects_age_and_retirement_is_idempotent(tmp_path: Path) -> None:
    root, blueprint = _repo(tmp_path)
    service = BlueprintLifecycleService(root=root, max_age_days=1)

    stale = service.inspect(blueprint, "FEAT-TEST", datetime(2026, 9, 4, tzinfo=timezone.utc))
    assert stale.stale is True
    assert "blueprint_age_exceeded" in stale.reasons

    retired = service.retire(blueprint, "FEAT-TEST", "superseded by current design", "FEAT-NEW")
    again = service.retire(blueprint, "FEAT-TEST", "superseded by current design", "FEAT-NEW")
    assert retired.state == "SUPERSEDED"
    assert again == retired
    assert blueprint.is_file()
    persisted = json.loads(
        (root / ".agents" / "state" / "work-items" / "FEAT-TEST" / "blueprint-lifecycle.json")
        .read_text(encoding="utf-8")
    )
    assert persisted["replacement_work_item"] == "FEAT-NEW"
