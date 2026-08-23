import os
import subprocess

import pytest

from conftest import ORIG_CWD, run_cli
from workflow_runtime.presentation.cli.commands._impl.provider import provider_data


def test_workflow_submit_alias_accepts_prompt(monkeypatch):
    monkeypatch.setenv("AIWF_TESTING_BYPASS_ENFORCER", "true")
    result = run_cli(
        "workflow",
        "submit",
        "--prompt",
        "fix runtime daemon singleton",
        timeout=15,
    )

    assert result.returncode == 0
    assert '"status": "ROUTED"' in result.stdout
    assert '"next_skill": "quick-fix"' in result.stdout
    assert not os.path.exists("docs/brainstorming/FEAT-312.md")


def test_runtime_start_is_singleton_when_state_is_active(monkeypatch):
    class ActiveState:
        def inspect(self):
            return {"active": True, "pid": 4242, "status": "ACTIVE"}

    popen_calls = []
    monkeypatch.setattr(provider_data, "RuntimeDaemonState", lambda: ActiveState())
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)))

    started, pid, status = provider_data.start_runtime_bus_daemon()

    assert started is False
    assert pid == 4242
    assert status == "already_running"
    assert popen_calls == []


def test_windows_autostart_does_not_create_visible_startup_cmd(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_data.platform, "system", lambda: "Windows")
    monkeypatch.setattr(provider_data, "_resolve_aiwf_project_root", lambda: str(tmp_path))
    monkeypatch.setattr(provider_data, "_runtime_pythonpath_root", lambda: str(tmp_path / "runtime"))
    monkeypatch.setattr(provider_data, "runtime_bus_autostart_target", lambda: "AIWF Runtime Daemon")
    startup_cmd = tmp_path / "Startup" / "AIWF Runtime Daemon.cmd"
    monkeypatch.setattr(provider_data, "runtime_bus_startup_folder_target", lambda: str(startup_cmd))
    monkeypatch.setattr(provider_data.sys, "executable", str(tmp_path / "python.exe"))

    def deny_schtasks(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
            stderr="Access is denied",
        )

    monkeypatch.setattr(subprocess, "run", deny_schtasks)

    with pytest.raises(RuntimeError, match="silent Windows autostart"):
        provider_data.enable_runtime_bus_autostart()

    assert not startup_cmd.exists()


def test_aiwf_skill_requires_native_prompt_gates():
    for path in [
        "skills/aiwf/SKILL.md",
        ".agents/skills/aiwf/SKILL.md",
        "public_export/skills/aiwf/SKILL.md",
    ]:
        with open(os.path.join(ORIG_CWD, path), "r", encoding="utf-8") as f:
            content = f.read()

        assert "NATIVE PROMPT GATES ONLY" in content
        assert "ask_question" in content
        assert 'aiwf prompt select --options "Continue|Cancel"' in content
        assert "MUST NOT be requested as the primary approval path" in content
        assert "InputValidationError" in content
        assert "raw JSON" in content
        assert "malformed `\\uXXXX`" in content


def test_ai_rules_require_prompt_tool_json_hygiene():
    for path in [
        "AI_RULES.md",
        ".agents/AI_RULES.md",
        "public_export/AI_RULES.md",
    ]:
        with open(os.path.join(ORIG_CWD, path), "r", encoding="utf-8") as f:
            content = f.read()

        assert "Tool Invocation JSON Hygiene" in content
        assert "MUST NOT hand-author raw JSON strings" in content
        assert "InputValidationError" in content
        assert "malformed `\\uXXXX` escape" in content
        assert "immediately retry through `aiwf prompt select" in content


def test_blueprint_quality_gate_requires_code_gate_line_budget_family_and_lint():
    for path in [
        "AI_RULES.md",
        ".agents/AI_RULES.md",
        "public_export/AI_RULES.md",
        "skills/quick-fix/SKILL.md",
        ".agents/skills/quick-fix/SKILL.md",
        "public_export/skills/quick-fix/SKILL.md",
        "skills/quick-feature/SKILL.md",
        ".agents/skills/quick-feature/SKILL.md",
        "public_export/skills/quick-feature/SKILL.md",
        "skills/plan-to-blueprint/SKILL.md",
        ".agents/skills/plan-to-blueprint/SKILL.md",
        "public_export/skills/plan-to-blueprint/SKILL.md",
        "skills/software-development-workflow/SKILL.md",
        ".agents/skills/software-development-workflow/SKILL.md",
        "public_export/skills/software-development-workflow/SKILL.md",
    ]:
        with open(os.path.join(ORIG_CWD, path), "r", encoding="utf-8") as f:
            content = f.read()

        assert "CODE_BLOCK_GATE" in content
        assert "500" in content
        assert "family" in content.lower()
        assert "language" in content.lower()
        assert "lint" in content.lower() or "typecheck" in content.lower()
