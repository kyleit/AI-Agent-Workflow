import hashlib
import json
from unittest.mock import patch

from pathlib import Path

from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    sync_blueprint_approval_metadata,
)
from workflow_runtime.presentation.cli.commands._impl.workflow.task_command_dispatcher import (
    _refresh_strict_code_block_gate,
)
from workflow_runtime.presentation.cli.commands.task_commands import (
    BlueprintCommand,
    ImplementCommand,
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


def test_approval_gate_refreshes_after_metadata_changes_blueprint_hash(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    blueprint = tmp_path / "docs" / "FEAT-612_blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    runner = tmp_path / "skills" / "strict-code-block-gate" / "scripts" / "run_strict_code_block_gate.py"
    runner.parent.mkdir(parents=True)
    runner.write_text("# test runner\n", encoding="utf-8")

    def write_gate(command, **_kwargs):
        output = Path(command[command.index("--output") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps({
                "decision": "PASS",
                "blueprint_full_sha256": hashlib.sha256(blueprint.read_bytes()).hexdigest(),
            }),
            encoding="utf-8",
        )
        return type("Completed", (), {"returncode": 0})()

    with patch(
        "workflow_runtime.presentation.cli.commands._impl.workflow.task_command_dispatcher.subprocess.run",
        side_effect=write_gate,
    ):
        ok, reason, result = _refresh_strict_code_block_gate(blueprint, "FEAT-612")

    assert ok is True
    assert reason == "strict_code_block_gate_refreshed"
    assert result["decision"] == "PASS"


def test_blueprint_and_implement_commands_propagate_blocked_exit_codes() -> None:
    from unittest.mock import patch
    from argparse import Namespace

    with patch(
        "workflow_runtime.presentation.cli.workflow_runtime.do_blueprint",
        return_value=3,
    ):
        assert BlueprintCommand().run(Namespace()) == 3
    with patch(
        "workflow_runtime.presentation.cli.workflow_runtime.do_implement_action",
        return_value=3,
    ):
        assert ImplementCommand().run(Namespace()) == 3
