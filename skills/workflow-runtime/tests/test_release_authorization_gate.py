from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def _load_gate():
    path = Path(__file__).parents[3] / "tools" / "aiwf-hooks" / "aiwf_gate.py"
    spec = importlib.util.spec_from_file_location("aiwf_gate_for_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _digest(root: Path, scope: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(scope):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256((root / relative).read_bytes()).digest())
        digest.update(b"\n")
    return digest.hexdigest()


def test_release_authorization_accepts_only_bound_scope(tmp_path: Path) -> None:
    gate = _load_gate()
    (tmp_path / ".agents" / "state" / "release").mkdir(parents=True)
    (tmp_path / ".agents" / "state" / "work-items" / "FIX-TEST").mkdir(parents=True)
    (tmp_path / "docs" / "features" / "workflow-runtime" / "blueprints").mkdir(parents=True)
    (tmp_path / "docs" / "debug").mkdir(parents=True)
    (tmp_path / "docs" / "verification").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "src" / "unrelated.py").write_text("print('wip')\n", encoding="utf-8")
    blueprint = tmp_path / "docs" / "features" / "workflow-runtime" / "blueprints" / "FIX-TEST_blueprint.md"
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    for report in (tmp_path / "docs" / "debug" / "FIX-TEST_debug.md", tmp_path / "docs" / "verification" / "FIX-TEST_verify.md"):
        report.write_text("---\nstatus: PASS\n---\n", encoding="utf-8")
    (tmp_path / ".agents" / "state" / "workflow.json").write_text(
        json.dumps({"active_workflow": "FIX-TEST", "work_item": {"id": "FIX-TEST"}}), encoding="utf-8"
    )
    scope = ["src/app.py"]
    (tmp_path / ".agents" / "state" / "release" / "1.2.3.json").write_text(
        json.dumps({"version": "1.2.3", "work_item": "FIX-TEST"}), encoding="utf-8"
    )
    (tmp_path / ".agents" / "state" / "release" / "authorization.json").write_text(
        json.dumps({
            "authorized": True,
            "operation": "release",
            "work_item": "FIX-TEST",
            "version": "1.2.3",
            "blueprint_path": "docs/features/workflow-runtime/blueprints/FIX-TEST_blueprint.md",
            "blueprint_sha256": hashlib.sha256(blueprint.read_bytes()).hexdigest(),
            "debug_path": "docs/debug/FIX-TEST_debug.md",
            "verification_path": "docs/verification/FIX-TEST_verify.md",
            "scope": scope,
            "scope_sha256": _digest(tmp_path, scope),
            "expires_at": "2099-01-01T00:00:00+00:00",
        }),
        encoding="utf-8",
    )

    assert gate._release_authorization_status(tmp_path, scope)[0] is True
    allowed, reason = gate._release_authorization_status(tmp_path, scope + ["src/unrelated.py"])
    assert allowed is False
    assert "exceed release scope" in reason


def test_release_authorization_rejects_expired_timestamp(tmp_path: Path) -> None:
    gate = _load_gate()
    (tmp_path / ".agents" / "state" / "release").mkdir(parents=True)
    (tmp_path / ".agents" / "state" / "workflow.json").write_text(
        json.dumps({"active_workflow": "FIX-TEST", "work_item": {"id": "FIX-TEST"}}), encoding="utf-8"
    )
    (tmp_path / ".agents" / "state" / "release" / "1.2.3.json").write_text(
        json.dumps({"version": "1.2.3"}), encoding="utf-8"
    )
    (tmp_path / ".agents" / "state" / "release" / "authorization.json").write_text(
        json.dumps({"authorized": True, "operation": "release", "work_item": "FIX-TEST", "version": "1.2.3", "expires_at": "2000-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    allowed, reason = gate._release_authorization_status(tmp_path)
    assert allowed is False
    assert "expired" in reason


def test_gate_subprocess_allows_scoped_release_without_bypass(tmp_path: Path) -> None:
    gate = _load_gate()
    (tmp_path / ".agents" / "state" / "release").mkdir(parents=True)
    (tmp_path / ".agents" / "state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "features" / "workflow-runtime" / "blueprints").mkdir(parents=True)
    (tmp_path / "docs" / "debug").mkdir(parents=True)
    (tmp_path / "docs" / "verification").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / ".agents" / "AI_RULES.md").write_text("rules\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "AIWF Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    (tmp_path / ".agents" / "state" / "workflow.json").write_text(
        json.dumps({"active_workflow": "FIX-TEST", "work_item": {"id": "FIX-TEST"}}), encoding="utf-8"
    )
    blueprint = tmp_path / "docs" / "features" / "workflow-runtime" / "blueprints" / "FIX-TEST_blueprint.md"
    blueprint.write_text("# Blueprint\n", encoding="utf-8")
    for report in (tmp_path / "docs" / "debug" / "FIX-TEST_debug.md", tmp_path / "docs" / "verification" / "FIX-TEST_verify.md"):
        report.write_text("---\nstatus: PASS\n---\n", encoding="utf-8")
    (tmp_path / ".agents" / "state" / "release" / "1.2.3.json").write_text(
        json.dumps({"version": "1.2.3"}), encoding="utf-8"
    )
    scope = ["src/app.py"]
    (tmp_path / "src" / "app.py").write_text("release\n", encoding="utf-8")
    (tmp_path / ".agents" / "state" / "release" / "authorization.json").write_text(
        json.dumps({
            "authorized": True,
            "operation": "release",
            "work_item": "FIX-TEST",
            "version": "1.2.3",
            "blueprint_path": "docs/features/workflow-runtime/blueprints/FIX-TEST_blueprint.md",
            "blueprint_sha256": hashlib.sha256(blueprint.read_bytes()).hexdigest(),
            "debug_path": "docs/debug/FIX-TEST_debug.md",
            "verification_path": "docs/verification/FIX-TEST_verify.md",
            "scope": scope,
            "scope_sha256": _digest(tmp_path, scope),
            "expires_at": "2099-01-01T00:00:00+00:00",
        }),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "src/app.py"], cwd=tmp_path, check=True)
    env = {key: value for key, value in os.environ.items() if key != "AIWF_BYPASS"}
    allowed = subprocess.run(
        [sys.executable, str(Path(__file__).parents[3] / "tools" / "aiwf-hooks" / "aiwf_gate.py"), "check-git"],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert allowed.returncode == 0, allowed.stderr

    (tmp_path / "src" / "unrelated.py").write_text("wip\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/unrelated.py"], cwd=tmp_path, check=True)
    blocked = subprocess.run(
        [sys.executable, str(Path(__file__).parents[3] / "tools" / "aiwf-hooks" / "aiwf_gate.py"), "check-git"],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert blocked.returncode == 1
    assert "exceed release scope" in blocked.stderr
