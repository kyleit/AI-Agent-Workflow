"""Real workspace and subprocess regressions for global, gate-free execution."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from workflow_runtime.application.security.capability_policy import Capability, decide_capability
from workflow_runtime.application.system.global_inventory import GlobalInstallationSnapshot
from workflow_runtime.application.system.project_sync import ProjectSyncPlanner
from workflow_runtime.application.system.shared_assets import skill_roots
from workflow_runtime.application.verification.evidence_gate_engine import EvidenceGateEngine
from workflow_runtime.infrastructure.session.session_bootstrap_guard import SessionBootstrapGuard
from workflow_runtime.presentation.cli.init_wizard import ScaffoldPlanner
from workflow_runtime.shared.gate_policy import gates_enforced

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIWF_GATE_MODE", raising=False)
    monkeypatch.setenv("AIWF_FRAMEWORK_ROOT", str(ROOT))


def test_session_does_not_create_skill_tree(tmp_path: Path) -> None:
    assert SessionBootstrapGuard(str(tmp_path), "real-session").initialize_workspace() == (True, "")
    assert not (tmp_path / ".agents/skills").exists()
    assert (tmp_path / ".agents/config/skill-registry.json").is_file()
    assert any((root / "aiwf/SKILL.md").is_file() for root in skill_roots(tmp_path))


def test_scaffold_uses_global_without_copy(tmp_path: Path) -> None:
    assert ScaffoldPlanner(str(tmp_path)).generate_scaffold({"git": {"initialize": False}})
    assert not (tmp_path / ".agents/skills").exists()
    assert json.loads((tmp_path / ".agents/project.json").read_text())["bridge_mode"] == "global_link"
    assert not (tmp_path / ".agents/githooks").exists()


def test_legacy_project_update_does_not_reinstall_skills(tmp_path: Path) -> None:
    snapshot = GlobalInstallationSnapshot(True, str(ROOT), str(ROOT / "skills"),
        str(ROOT / "AI_RULES.md"), str(ROOT / "tools"), "test", {}, ["skills/aiwf"])
    plan = ProjectSyncPlanner().plan(tmp_path, snapshot)
    assert plan.reason == "GLOBAL_BRIDGE_METADATA_ONLY"
    assert ProjectSyncPlanner().sync(plan, snapshot) == []
    assert not (tmp_path / ".agents/skills").exists()


def test_gate_disabled_is_skipped_not_approved(tmp_path: Path) -> None:
    assert not gates_enforced()
    assert EvidenceGateEngine(str(tmp_path)).evaluate_gate("Gate2_BlueprintApproval", {}) == "SKIPPED"
    decision = decide_capability("sandbox", Capability.LOCAL_WRITE, False)
    assert decision.allowed and not decision.requires_approval
    assert not (tmp_path / ".agents/state/approvals.json").exists()


def test_enforcement_remains_explicit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AIWF_GATE_MODE", "enforce")
    assert gates_enforced()
    assert not decide_capability("autonomous", Capability.LOCAL_WRITE, False).allowed
    assert EvidenceGateEngine(str(tmp_path)).evaluate_gate("Gate2_BlueprintApproval", {}) != "SKIPPED"


def test_implementation_needs_no_blueprint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from workflow_runtime.presentation.cli.commands._impl.project_manager import do_implement_action
    monkeypatch.chdir(tmp_path)
    assert do_implement_action(argparse.Namespace()) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["data"]["gate_status"] == "SKIPPED"
    assert result["next_action"]["command"] is None  # no automatic self-dispatch loop
    assert not (tmp_path / ".agents/state/work-items").exists()


def test_real_source_and_claude_hooks_allow_unapproved_edit(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "AI_RULES.md").write_text("# Project rules\n")
    gate = ROOT / "tools/aiwf-hooks/aiwf_gate.py"
    result = subprocess.run([sys.executable, str(gate), "check-file", "src/new.py"],
        cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    guard = ROOT / "tools/aiwf-hooks/claude_source_write_guard.py"
    result = subprocess.run([sys.executable, str(guard)], cwd=tmp_path,
        input=json.dumps({"cwd": str(tmp_path), "tool_input": {"file_path": "src/new.py"}}),
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_real_cli_init_and_implement_without_skill_copy(tmp_path: Path) -> None:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "skills/workflow-runtime"))
    for args in (["init", "--non-interactive"], ["implement"], ["gate", "status"],
                 ["blueprint", "--approve"],
                 ["start", "--skill", "blueprint-to-implementation", "--command", "implement"]):
        result = subprocess.run([sys.executable, "-m", "workflow_runtime", *args],
            cwd=tmp_path, env=env, capture_output=True, text=True, check=False, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        assert not (tmp_path / ".agents/skills").exists()


def test_continue_skips_old_approval_without_fabrication(tmp_path: Path) -> None:
    from workflow_runtime.presentation.cli.commands._impl.workflow.continuation import continue_workflow
    state = tmp_path / ".agents/state"
    state.mkdir(parents=True)
    (state / "workflow.json").write_text(json.dumps({"active_workflow": "TEST-1", "active_phase": "blueprint",
        "waiting_for": "blueprint_approval", "requires_approval": True}))
    result = continue_workflow(tmp_path)
    assert result.status == "success"
    assert result.next_action.automatic
    assert not (state / "approvals.json").exists()


def test_execution_no_longer_requires_workflow_or_tester_role(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from workflow_runtime.application.use_cases.execution_manager import ExecutionManager
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AIWF_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("AIWF_WORKFLOW_ID", raising=False)
    allowed, reason = ExecutionManager.validate_request({"command": "pytest", "arguments": ["-q"],
        "working_directory": str(tmp_path), "owner_agent_id": "codex"})
    assert allowed, reason


def test_git_hooks_allow_real_commit_and_local_push_without_approval(tmp_path: Path) -> None:
    def git(*args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        return result
    git("init")
    git("config", "core.hooksPath", str(ROOT / "tools/githooks"))
    (tmp_path / "AI_RULES.md").write_text("# Test workspace\n")
    (tmp_path / "new.py").write_text("print('real hook test')\n")
    git("add", "AI_RULES.md", "new.py")
    git("-c", "user.name=AIWF test", "-c", "user.email=test@example.invalid", "commit", "-m", "hook test")
    remote = tmp_path / "local-remote.git"
    git("init", "--bare", str(remote))
    git("push", str(remote), "HEAD:refs/heads/test")
    assert not (tmp_path / ".agents/state/approvals.json").exists()


def test_process_enforcer_is_off_even_with_legacy_force_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from workflow_runtime.application.verification.test_enforcer import patched_run
    monkeypatch.setenv("AIWF_FORCE_ENFORCE", "true")
    result = patched_run([sys.executable, "-c", "print('executed')"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip() == "executed"


def test_minimal_project_status_keeps_callers_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from workflow_runtime.presentation.cli.commands._impl.shared_helpers import get_current_project_context
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents/project.json").write_text("{}")
    assert Path(get_current_project_context()["absolute_path"]).resolve() == tmp_path.resolve()
