from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aiwf_gate  # noqa: E402


def _write_workflow(root: Path, work_item: str = "FEAT-001") -> None:
    state = root / ".agents" / "state"
    state.mkdir(parents=True)
    (state / "workflow.json").write_text(
        json.dumps({
            "active_workflow": work_item,
            "active_phase": "implementation",
            "status": "IN_PROGRESS",
        }),
        encoding="utf-8",
    )


def test_explicit_authorization_rejects_absolute_external_blueprint(tmp_path: Path) -> None:
    _write_workflow(tmp_path)
    auth = tmp_path / ".agents" / "state" / "source-write-authorization.json"
    auth.write_text(
        json.dumps({
            "authorized": True,
            "work_item": "FEAT-001",
            "blueprint_path": "C:/Users/Kyle/.gemini/old-blueprint.md",
            "blueprint_sha256": "stale",
        }),
        encoding="utf-8",
    )

    allowed, reason = aiwf_gate._explicit_authorization(tmp_path)

    assert allowed is False
    assert "repo-relative" in reason


def test_explicit_authorization_requires_current_blueprint_hash(tmp_path: Path) -> None:
    _write_workflow(tmp_path)
    blueprint = tmp_path / "docs" / "features" / "feature" / "blueprints" / "FEAT-001_blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    auth = tmp_path / ".agents" / "state" / "source-write-authorization.json"
    auth.write_text(
        json.dumps({
            "authorized": True,
            "work_item": "FEAT-001",
            "blueprint_path": "docs/features/feature/blueprints/FEAT-001_blueprint.md",
            "blueprint_sha256": "stale",
        }),
        encoding="utf-8",
    )

    allowed, reason = aiwf_gate._explicit_authorization(tmp_path)

    assert allowed is False
    assert "hash is stale or missing" in reason


def test_explicit_authorization_rejects_stale_work_item_without_active_workflow(tmp_path: Path) -> None:
    state = tmp_path / ".agents" / "state"
    state.mkdir(parents=True)
    (state / "workflow.json").write_text(
        json.dumps({
            "active_workflow": None,
            "active_phase": None,
            "status": "completed",
            "work_item": {"id": "FEAT-001"},
        }),
        encoding="utf-8",
    )
    blueprint = tmp_path / "docs" / "features" / "feature" / "blueprints" / "FEAT-001_blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    auth = state / "source-write-authorization.json"
    auth.write_text(
        json.dumps({
            "authorized": True,
            "work_item": "FEAT-001",
            "blueprint_path": "docs/features/feature/blueprints/FEAT-001_blueprint.md",
            "blueprint_sha256": aiwf_gate._sha256_file(blueprint),
        }),
        encoding="utf-8",
    )

    allowed, reason = aiwf_gate._explicit_authorization(tmp_path)

    assert allowed is False
    assert "active workflow" in reason


def test_explicit_authorization_rejects_noncanonical_blueprint(tmp_path: Path) -> None:
    _write_workflow(tmp_path)
    blueprint = tmp_path / "docs" / "features" / "feature" / "BLUEPRINT.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    auth = tmp_path / ".agents" / "state" / "source-write-authorization.json"
    auth.write_text(
        json.dumps({
            "authorized": True,
            "work_item": "FEAT-001",
            "blueprint_path": "docs/features/feature/BLUEPRINT.md",
            "blueprint_sha256": aiwf_gate._sha256_file(blueprint),
        }),
        encoding="utf-8",
    )

    allowed, reason = aiwf_gate._explicit_authorization(tmp_path)

    assert allowed is False
    assert "not canonical" in reason
