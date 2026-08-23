from pathlib import Path

from workflow_runtime.application.verification.test_enforcer import is_test_command
from workflow_runtime.presentation.cli.workflow_runtime import (
    _audit_workflow_document_quality,
    _capture_release_metadata_hashes,
    _capture_tree_hashes,
    _diff_tree_hashes,
    _has_release_metadata_changes,
    _has_workflow_report_changes,
    _has_workflow_documentation_changes,
    _prepare_agy_prompt_and_mode,
    _runtime_bus_response,
    _sanitize_artifact_tree,
    _sanitize_runtime_value,
    _read_json_file,
)
from workflow_runtime.presentation.cli.commands import build_registry


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_ai_rules_do_not_stop_after_clear_workflow_detection() -> None:
    for rel_path in ("AI_RULES.md", ".agents/AI_RULES.md"):
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")

        assert "detection summary and STOP" not in content
        assert "Do not stop after detection for a clear request" in content
        assert "Dispatch to the selected Skill in the same turn" in content
        assert "MUST NOT emit local absolute paths" in content


def test_quick_feature_does_not_require_pre_blueprint_confirmation() -> None:
    for rel_path in ("skills/quick-feature/SKILL.md", ".agents/skills/quick-feature/SKILL.md"):
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")

        assert "selected Skill requires confirmation" not in content
        assert "Clear raw requests are routed automatically" in content
        assert "Plain chat approval is not valid and must not be used to unlock implementation" in content
        assert "Do not print drive-letter paths or `file:///` links" in content


def test_agy_prompt_text_does_not_trigger_test_command_detection() -> None:
    cmd = [
        "agy",
        "--dangerously-skip-permissions",
        "--model",
        "gemini-3.6-flash-high",
        "--add-dir",
        ".",
        "--print-timeout",
        "10m",
        "--print",
        "/aiwf test skills and verify no blueprint no code behavior",
    ]

    assert is_test_command(cmd) is False


def test_real_pytest_command_still_triggers_test_command_detection() -> None:
    assert is_test_command(["python", "-m", "pytest", "-v"]) is True


def test_aiwf_agy_prompt_is_forced_to_plan_mode_before_blueprint_approval() -> None:
    prompt, mode, guard_applied = _prepare_agy_prompt_and_mode(
        "/aiwf fix all skills and mirror implementation",
        "",
        {},
    )

    assert guard_applied is True
    assert mode == "plan"
    assert "NO BLUEPRINT - NO CODE" in prompt
    assert prompt.endswith("/aiwf fix all skills and mirror implementation")


def test_plain_agy_prompt_is_normalized_to_aiwf_before_blueprint_approval() -> None:
    prompt, mode, guard_applied = _prepare_agy_prompt_and_mode(
        "fix all skills and mirror implementation",
        "",
        {},
    )

    assert guard_applied is True
    assert mode == "plan"
    assert "even when the user did not type /aiwf" in prompt
    assert "Do not stop after workflow detection" in prompt
    assert "Never emit local absolute paths or file:/// links" in prompt
    assert prompt.endswith("/aiwf fix all skills and mirror implementation")


def test_plain_agy_prompt_can_explicitly_bypass_aiwf_guard_for_raw_runs() -> None:
    prompt, mode, guard_applied = _prepare_agy_prompt_and_mode(
        "summarize this text only",
        "",
        {"allow_raw_agy_prompt": True},
    )

    assert guard_applied is False
    assert mode == ""
    assert prompt == "summarize this text only"


def test_aiwf_agy_prompt_keeps_source_write_mode_when_explicitly_approved() -> None:
    prompt, mode, guard_applied = _prepare_agy_prompt_and_mode(
        "/aiwf implement approved blueprint",
        "implement",
        {"blueprint_approved": True},
    )

    assert guard_applied is False
    assert mode == "implement"
    assert prompt == "/aiwf implement approved blueprint"


def test_runtime_bus_response_redacts_local_paths_from_agy_output() -> None:
    response = _runtime_bus_response(
        "OK",
        "agy.run",
        "k",
        "see file:///Users/developer/scratch/out.md",
        {
            "output": "wrote /Users/developer/.gemini/antigravity-cli/scratch/x and /Volumes/Workspace/project/file.py",
            "stderr": "${USERPROFILE}\\scratch\\out.txt",
        },
    )
    rendered = str(response)

    assert "file:///Users" not in rendered
    assert "/Users/developer" not in rendered
    assert "/Volumes/Workspace" not in rendered
    assert "${USERPROFILE}" not in rendered
    assert "[local-file-url-redacted]" in rendered
    assert "[local-path-redacted]" in rendered


def test_sanitize_runtime_value_recurses_through_collections() -> None:
    value = _sanitize_runtime_value({"items": ["file:///Users/developer/a", {"path": "/tmp/secret"}]})

    assert value == {"items": ["[local-file-url-redacted]", {"path": "[local-path-redacted]"}]}


def test_runtime_request_json_reader_accepts_windows_utf8_bom(tmp_path) -> None:
    request = tmp_path / "runtime.request.json"
    request.write_text('{"type":"RUNTIME_COMMAND"}\n', encoding="utf-8-sig")

    assert _read_json_file(str(request)) == {"type": "RUNTIME_COMMAND"}


def test_documentation_change_detection_requires_docs_tree_change() -> None:
    before = {"skills/example/SKILL.md": "a", "docs/features/demo/plan.md": "old"}
    after = {"skills/example/SKILL.md": "b", "docs/features/demo/plan.md": "old"}

    assert _diff_tree_hashes(before, after) == ["skills/example/SKILL.md"]
    assert _has_workflow_documentation_changes(before, after) is False

    after["docs/features/demo/plan.md"] = "new"

    assert _has_workflow_documentation_changes(before, after) is True


def test_tree_hashes_use_portable_forward_slash_paths(tmp_path) -> None:
    artifact = tmp_path / "docs" / "features" / "demo" / "README.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Demo\n\nPortable path key fixture.\n", encoding="utf-8")

    assert "docs/features/demo/README.md" in _capture_tree_hashes(str(tmp_path), ("docs",))


def test_artifact_tree_sanitizer_redacts_docs_files(tmp_path) -> None:
    report = tmp_path / "docs" / "features" / "demo" / "reports" / "report.md"
    report.parent.mkdir(parents=True)
    report.write_text("rootdir: /Volumes/Workspace/project\nscratch: file:///Users/developer/a.md\n", encoding="utf-8")

    changed = _sanitize_artifact_tree(str(tmp_path), ("docs",))

    assert changed == ["docs/features/demo/reports/report.md"]
    content = report.read_text(encoding="utf-8")
    assert "/Volumes/Workspace" not in content
    assert "file:///Users" not in content
    assert "[local-path-redacted]" in content
    assert "[local-file-url-redacted]" in content


def test_workflow_document_quality_requires_blueprint_code_block(tmp_path) -> None:
    feature_root = tmp_path / "docs" / "features" / "demo"
    blueprint = feature_root / "blueprints" / "bp.md"
    blueprint.parent.mkdir(parents=True)
    (feature_root / "README.md").write_text(
        "# Demo\n\nSemantic family index with enough detail for audit coverage.\n"
        "Links: blueprints/bp.md. This index is intentionally detailed enough to pass "
        "the document-thickness gate while still staying small for a focused unit test.\n",
        encoding="utf-8",
    )
    blueprint.write_text(
        "# Blueprint\n\n"
        "## File-by-File Change Matrix\n"
        "## API & Interface Signatures\n"
        "## Data Schemas\n"
        "## Targeted Test Strategy\n"
        "## Risk Mitigation\n"
        "## Acceptance Criteria\n"
        "## Internal Review Evidence\n",
        encoding="utf-8",
    )

    issues = _audit_workflow_document_quality(str(tmp_path))

    assert any("missing fenced code block" in issue for issue in issues)

    blueprint.write_text(
        "# Blueprint\n\n"
        "## File-by-File Change Matrix\n"
        "## API & Interface Signatures\n"
        "## Data Schemas\n"
        "```python\n"
        "def demo() -> None:\n"
        "    pass\n"
        "```\n"
        "## Targeted Test Strategy\n"
        "## Risk Mitigation\n"
        "## Acceptance Criteria\n"
        "## Internal Review Evidence\n",
        encoding="utf-8",
    )

    assert _audit_workflow_document_quality(str(tmp_path)) == []


def test_workflow_document_quality_requires_standard_chain_when_requested(tmp_path) -> None:
    feature_root = tmp_path / "docs" / "features" / "workflow-test"
    blueprint = feature_root / "blueprints" / "FEAT-001_workflow_test_blueprint.md"
    blueprint.parent.mkdir(parents=True)
    (feature_root / "README.md").write_text(
        "# Workflow Test\n\nSemantic feature index for a workflow-test family. "
        "It links roadmap, architecture review, brainstorming, plan, and blueprint artifacts.\n",
        encoding="utf-8",
    )
    blueprint.write_text(
        "# Blueprint\n\n"
        "## File-by-File Change Matrix\n"
        "## API & Interface Signatures\n"
        "## Data Schemas\n"
        "```python\n"
        "def demo() -> None:\n"
        "    pass\n"
        "```\n"
        "## Targeted Test Strategy\n"
        "## Risk Mitigation\n"
        "## Acceptance Criteria\n"
        "## Internal Review Evidence\n",
        encoding="utf-8",
    )

    issues = _audit_workflow_document_quality(str(tmp_path), require_standard_chain=True)

    assert any("roadmaps" in issue for issue in issues)
    assert any("architecture-reviews" in issue for issue in issues)
    assert any("brainstorming" in issue for issue in issues)
    assert any("plans" in issue for issue in issues)
    assert any("master" in issue for issue in issues)
    assert any("phase-NN" in issue for issue in issues)

    for phase_dir in ("roadmaps", "architecture-reviews"):
        artifact = feature_root / phase_dir / f"FEAT-001_workflow_test_{phase_dir}.md"
        artifact.parent.mkdir(parents=True)
        artifact.write_text(
            "# Artifact\n\n"
            "Detailed content with enough evidence, traceability, failed-point repair notes, "
            "document-compliance score, and relative-path scan result for the audit gate.\n\n"
            "## Internal Review Evidence\nPASS\n",
            encoding="utf-8",
        )
    for phase_dir in ("brainstorming", "plans"):
        for scope_dir in ("master", "phase-01-core"):
            artifact = feature_root / phase_dir / scope_dir / f"FEAT-001_workflow_test_{phase_dir}.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text(
                "# Artifact\n\n"
                "Detailed content with enough evidence, traceability, failed-point repair notes, "
                "document-compliance score, and relative-path scan result for the audit gate.\n\n"
                "## Internal Review Evidence\nPASS\n",
                encoding="utf-8",
            )
    phase_blueprint = feature_root / "blueprints" / "phase-01-core" / "FEAT-001_workflow_test_phase_blueprint.md"
    phase_blueprint.parent.mkdir(parents=True)
    phase_blueprint.write_text(blueprint.read_text(encoding="utf-8"), encoding="utf-8")
    master_blueprint = feature_root / "blueprints" / "master" / "FEAT-001_workflow_test_master_blueprint.md"
    master_blueprint.parent.mkdir(parents=True)
    master_blueprint.write_text(blueprint.read_text(encoding="utf-8"), encoding="utf-8")

    assert _audit_workflow_document_quality(str(tmp_path), require_standard_chain=True) == []


def test_placeholder_scan_does_not_reject_todo_feature_names(tmp_path) -> None:
    feature_root = tmp_path / "docs" / "features" / "todo-cli"
    blueprint = feature_root / "blueprints" / "FEAT-001_todo_cli_blueprint.md"
    blueprint.parent.mkdir(parents=True)
    (feature_root / "README.md").write_text(
        "# Todo CLI\n\nSemantic index for the todo CLI feature family with relative links, review traceability, "
        "artifact inventory, scope boundaries, and enough prose to pass the document-thickness gate.\n",
        encoding="utf-8",
    )
    blueprint.write_text(
        "# Todo CLI Blueprint\n\n"
        "## File-by-File Change Matrix\n"
        "## API & Interface Signatures\n"
        "## Data Schemas\n"
        "```python\n"
        "def add_todo(title: str) -> dict:\n"
        "    return {\"title\": title}\n"
        "```\n"
        "## Targeted Test Strategy\n"
        "## Risk Mitigation\n"
        "## Acceptance Criteria\n"
        "## Internal Review Evidence\n",
        encoding="utf-8",
    )

    assert _audit_workflow_document_quality(str(tmp_path)) == []

    blueprint.write_text(blueprint.read_text(encoding="utf-8") + "\nTODO: fill later\n", encoding="utf-8")

    assert any("placeholder marker" in issue for issue in _audit_workflow_document_quality(str(tmp_path)))


def test_placeholder_scan_rejects_markers_in_any_markdown_artifact(tmp_path) -> None:
    feature_root = tmp_path / "docs" / "features" / "demo"
    blueprint = feature_root / "blueprints" / "bp.md"
    blueprint.parent.mkdir(parents=True)
    (feature_root / "README.md").write_text(
        "# Demo\n\nThis semantic index has enough detail but includes TODO as a forbidden marker.\n",
        encoding="utf-8",
    )
    blueprint.write_text(
        "# Blueprint\n\n"
        "## File-by-File Change Matrix\n"
        "## API & Interface Signatures\n"
        "## Data Schemas\n"
        "```python\n"
        "def demo() -> None:\n"
        "    pass\n"
        "```\n"
        "## Targeted Test Strategy\n"
        "## Risk Mitigation\n"
        "## Acceptance Criteria\n"
        "## Internal Review Evidence\n",
        encoding="utf-8",
    )

    assert any("README.md: contains placeholder marker" in issue for issue in _audit_workflow_document_quality(str(tmp_path)))


def test_document_quality_rejects_rubber_stamp_review_and_bad_completion_report(tmp_path) -> None:
    feature_root = tmp_path / "docs" / "features" / "webrdp"
    master_blueprint = feature_root / "blueprints" / "master" / "blueprint.md"
    phase_blueprint = feature_root / "blueprints" / "phase-01-vm-streaming" / "blueprint.md"
    review = feature_root / "architecture-reviews" / "REV-004_blueprint_review.md"
    report = tmp_path / "docs" / "reports" / "FIX-VM-STREAMING_completion_report.md"
    for path in (master_blueprint, phase_blueprint, review, report):
        path.parent.mkdir(parents=True, exist_ok=True)

    (feature_root / "README.md").write_text(
        "# WebRDP\n\nSemantic feature index with enough detail, traceability, and relative artifact links.\n",
        encoding="utf-8",
    )
    blueprint_text = (
        "# Blueprint\n\n"
        "## File-by-File Change Matrix\n"
        "## API & Interface Signatures\n"
        "## Data Schemas\n"
        "```go\n"
        "func connectGuacamole() error { return nil }\n"
        "```\n"
        "## Targeted Test Strategy\n"
        "## Risk Mitigation\n"
        "## Acceptance Criteria\n"
        "## Internal Review Evidence\n"
        "| Field | Evidence |\n|---|---|\n"
        "| Reviewer Roles | Architect / Auditor |\n"
        "| Source Artifacts Reviewed | docs/features/webrdp/blueprints/master/blueprint.md |\n"
        "| Checklist Result | PASS |\n"
        "| Failed Points | None |\n"
        "| Revision Scope | None |\n"
        "| Re-review Count | 0 |\n"
        "| Document Compliance Score | 100/100 |\n"
        "| Relative Path Scan | PASS |\n"
        "| Final Result | PASS |\n"
    )
    master_blueprint.write_text(blueprint_text, encoding="utf-8")
    phase_blueprint.write_text(blueprint_text, encoding="utf-8")
    review.write_text(
        "# Architecture Review REV-004 â€“ Technical Design Blueprint Assessment\n\n"
        "- **Status**: PASS (Score: 100/100)\n"
        "- [Blueprint](file:///e:/repo/docs/features/webrdp/blueprints/master/blueprint.md)\n\n"
        "## Comprehensive Assessment Checklist\n"
        "| Criteria | Result | Evidence |\n|---|---|---|\n"
        "| Zero Placeholders | PASS | Zero occurrences in both Blueprint files. |\n"
        "| Code Block Completeness | PASS | Full working Go code specs. |\n\n"
        "## Internal Review Evidence\n"
        "| Field | Evidence |\n|---|---|\n"
        "| Reviewer Roles | Lead Architect / Auditor |\n"
        "| Source Artifacts Reviewed | Master Blueprint & Phase 01 Blueprint |\n"
        "| Failed Points | None |\n"
        "| Document Compliance Score | 100/100 |\n"
        "| Relative Path Scan | PASS |\n"
        "| Final Result | PASS |\n",
        encoding="utf-8",
    )
    report.write_text(
        "# Verification & Final Completion Report â€“ VM Web Streaming Fix\n\n"
        "- **Status**: VERIFIED & COMPLETED\n"
        "- **Feature Family**: [webrdp](file:///e:/repo/docs/features/webrdp/README.md)\n"
        "- **Unit Test Execution**: `go test -v ./...` -> PASS (All packages passed cleanly).\n"
        "```text\n"
        "? sandbox-runner/presentation/dashboard [no test files]\n"
        "```\n",
        encoding="utf-8",
    )

    issues = _audit_workflow_document_quality(str(tmp_path))

    assert any("local absolute path or local-file URL" in issue for issue in issues)
    assert any("mojibake" in issue for issue in issues)
    assert any("rubber-stamp PASS" in issue for issue in issues)
    assert any("claims test coverage from no-test-files output" in issue for issue in issues)
    assert any("final completion claim lacks live runtime evidence" in issue for issue in issues)


def test_release_and_post_release_cli_surface_matches_full_flow() -> None:
    registry = build_registry()
    registry.build_parser()

    command_names = {cmd.meta().name for cmd in registry.get_all()}

    assert "release" in command_names
    assert "post-release" in command_names
    release_cmd = next(cmd for cmd in registry.get_all() if cmd.meta().name == "release")
    post_release_cmd = next(cmd for cmd in registry.get_all() if cmd.meta().name == "post-release")

    release_args = release_cmd.parse(["validate", "--dry-run"])
    post_release_args = post_release_cmd.parse(["run", "--version", "1.2.3", "--commit", "abc123"])

    assert release_args.action == "validate"
    assert release_args.dry_run is True
    assert post_release_args.action == "run"
    assert post_release_args.version == "1.2.3"
    assert post_release_args.commit == "abc123"


def test_agy_run_rejects_direct_agents_skills_mirror_edits(tmp_path, monkeypatch) -> None:
    from workflow_runtime.presentation.cli.commands._impl.update import update_source_git

    mirror_file = tmp_path / ".agents" / "skills" / "demo" / "SKILL.md"
    mirror_file.parent.mkdir(parents=True)
    mirror_file.write_text("# Demo\n\nOriginal installed mirror content.\n", encoding="utf-8")

    def fake_run(*_args, **_kwargs):
        mirror_file.write_text("# Demo\n\nIllegally edited installed mirror content.\n", encoding="utf-8")
        return type("Proc", (), {"returncode": 0, "stdout": "edited mirror", "stderr": ""})()

    monkeypatch.setattr(update_source_git.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)

    payload = {
        "type": "RUNTIME_COMMAND",
        "command": "agy.run",
        "idempotency_key": "mirror-edit-test",
        "args": {
            "prompt": "summarize only",
            "allow_raw_agy_prompt": True,
            "cwd": ".",
        },
    }

    try:
        update_source_git.execute_runtime_bus_request(payload)
        assert False, "mirror edit should be rejected"
    except ValueError as exc:
        assert "forbidden installed mirror changes" in str(exc)

    assert mirror_file.read_text(encoding="utf-8") == "# Demo\n\nOriginal installed mirror content.\n"


def test_release_metadata_gate_requires_version_or_changelog_change(tmp_path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    manifest = tmp_path / "MANIFEST.json"
    changelog.write_text("# Changelog\n\n## [0.1.0]\n", encoding="utf-8")
    manifest.write_text('{"version":"0.1.0"}\n', encoding="utf-8")

    before = _capture_release_metadata_hashes(str(tmp_path))

    assert _has_release_metadata_changes(before, _capture_release_metadata_hashes(str(tmp_path))) is False

    changelog.write_text("# Changelog\n\n## [0.1.1]\n- Release gate fix.\n", encoding="utf-8")

    assert _has_release_metadata_changes(before, _capture_release_metadata_hashes(str(tmp_path))) is True


def test_release_report_gate_accepts_semantic_feature_report_paths() -> None:
    assert _has_workflow_report_changes(["docs/features/demo/reports/REL-001_report.md"]) is True
    assert _has_workflow_report_changes(["docs/reports/REL-001_report.md"]) is True
    assert _has_workflow_report_changes(["docs/features/demo/blueprints/REL-001_blueprint.md"]) is False
