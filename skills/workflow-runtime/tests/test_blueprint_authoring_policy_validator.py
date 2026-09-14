import json
from pathlib import Path

from workflow_runtime.application.workflow.blueprint_authoring_policy_validator import (
    BlueprintAuthoringPolicyValidator,
)


def test_recent_script_that_writes_blueprint_is_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    skill = workspace / ".agents" / "skills" / "aiwf" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill\n", encoding="utf-8")
    blueprint = workspace / "docs" / "features" / "demo" / "blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    brain = tmp_path / "brain"
    scratch = brain / "conversation" / "scratch"
    scratch.mkdir(parents=True)
    script = scratch / "sync.py"
    script.write_text(
        "from pathlib import Path\n"
        "Path(r'" + str(workspace) + "').joinpath('docs/features/demo/blueprint.md')"
        ".write_text('generated blueprint')\n",
        encoding="utf-8",
    )

    result = BlueprintAuthoringPolicyValidator().validate(
        workspace,
        blueprint,
        brain_roots=[brain],
    )

    assert result.passed is False
    assert result.blocking_findings[0].startswith("script_authored_document_detected:")


def test_read_only_validation_script_is_allowed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    skill = workspace / ".agents" / "skills" / "aiwf" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill\n", encoding="utf-8")
    blueprint = workspace / "docs" / "features" / "demo" / "blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    brain = tmp_path / "brain"
    scratch = brain / "conversation" / "scratch"
    scratch.mkdir(parents=True)
    (scratch / "validate.py").write_text(
        "from pathlib import Path\n"
        "print(Path(r'" + str(blueprint) + "').read_text())\n",
        encoding="utf-8",
    )

    result = BlueprintAuthoringPolicyValidator().validate(
        workspace,
        blueprint,
        brain_roots=[brain],
    )

    assert result.passed is True
    assert result.blocking_findings == []


def test_any_recent_workspace_writer_is_blocked_even_without_document_markers(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    skill = workspace / ".agents" / "skills" / "aiwf" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill\n", encoding="utf-8")
    blueprint = workspace / "docs" / "features" / "demo" / "blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    brain = tmp_path / "brain"
    scratch = brain / "conversation" / "scratch"
    scratch.mkdir(parents=True)
    (scratch / "fix_one_line.py").write_text(
        "from pathlib import Path\n"
        "Path(r'" + str(workspace) + "').joinpath('notes.txt').write_text('x')\n",
        encoding="utf-8",
    )

    result = BlueprintAuthoringPolicyValidator().validate(
        workspace,
        blueprint,
        brain_roots=[brain],
    )

    assert result.passed is False
    assert result.blocking_findings[0].startswith("script_authored_document_detected:")


def test_recent_agy_transcript_inline_writer_is_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    skill = workspace / ".agents" / "skills" / "aiwf" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill\n", encoding="utf-8")
    blueprint = workspace / "docs" / "features" / "demo" / "blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    brain = tmp_path / "brain"
    transcript = brain / "conversation" / ".system_generated" / "logs" / "transcript_full.jsonl"
    transcript.parent.mkdir(parents=True)
    command = (
        "python -c \"from pathlib import Path; Path('"
        + str(workspace)
        + "').joinpath('docs/features/demo/blueprint.md').write_text('generated')\""
    )
    transcript.write_text(
        json.dumps({"tool_calls": [{"name": "run_command", "args": {"CommandLine": command}}]})
        + "\n",
        encoding="utf-8",
    )

    result = BlueprintAuthoringPolicyValidator().validate(
        workspace,
        blueprint,
        brain_roots=[brain],
    )

    assert result.passed is False
    assert result.blocking_findings[0].startswith("inline_script_authored_document_detected:")


def test_read_only_agy_transcript_command_is_allowed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    skill = workspace / ".agents" / "skills" / "aiwf" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill\n", encoding="utf-8")
    blueprint = workspace / "docs" / "features" / "demo" / "blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    brain = tmp_path / "brain"
    transcript = brain / "conversation" / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    command = "python -c \"print(open('" + str(blueprint) + "').read())\""
    transcript.write_text(
        json.dumps({"tool_calls": [{"name": "run_command", "args": {"CommandLine": command}}]})
        + "\n",
        encoding="utf-8",
    )

    result = BlueprintAuthoringPolicyValidator().validate(
        workspace,
        blueprint,
        brain_roots=[brain],
    )

    assert result.passed is True
