from pathlib import Path

from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    sync_blueprint_approval_metadata,
)


def test_blueprint_approval_sync_updates_frontmatter_and_hash(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text(
        "---\nfeature_id: FEAT-603\nstatus: AWAITING_OWNER_APPROVAL\n---\n# Blueprint\n",
        encoding="utf-8",
    )

    digest = sync_blueprint_approval_metadata(
        str(blueprint), "2026-09-02T12:00:00+07:00"
    )

    content = blueprint.read_text(encoding="utf-8")
    assert "status: APPROVED" in content
    assert "approved_at: 2026-09-02T12:00:00+07:00" in content
    assert "approved_by: user" in content
    assert digest


def test_blueprint_approval_sync_adds_frontmatter_when_missing(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text("# Blueprint\n", encoding="utf-8")

    sync_blueprint_approval_metadata(str(blueprint), "2026-09-02T12:00:00+07:00")

    content = blueprint.read_text(encoding="utf-8")
    assert content.startswith("---\nstatus: APPROVED\n")
