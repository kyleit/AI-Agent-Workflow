"""Focused regressions for the package entrypoint and Windows file writes."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from workflow_runtime.infrastructure.filesystem.atomic_writer import write_json_atomic


RUNTIME_PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_module_entrypoint_works_from_temporary_workspace(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(RUNTIME_PACKAGE_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "workflow_runtime", "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "provider" in result.stdout
    assert "state" in result.stdout


def test_legacy_modules_resolve_to_canonical_package_modules() -> None:
    expected = {
        "patch_applier": "workflow_runtime.infrastructure.filesystem.patch_applier",
        "worker_manager": "workflow_runtime.infrastructure.execution.worker_manager",
        "dag_planner": "workflow_runtime.application.workflow.dag_planner",
        "lock_manager": "workflow_runtime.infrastructure.persistence.lock_manager",
        "orchestrator": "workflow_runtime.application.use_cases.orchestrator",
    }

    for legacy_name, canonical_name in expected.items():
        module = importlib.import_module(legacy_name)
        assert module.__name__ == canonical_name


def test_atomic_writer_serializes_concurrent_replacements(tmp_path: Path) -> None:
    target = tmp_path / "concurrent.json"
    errors: list[Exception] = []

    def write_data(index: int) -> None:
        try:
            write_json_atomic(str(target), {"index": index})
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=write_data, args=(index,)) for index in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert json.loads(target.read_text(encoding="utf-8"))["index"] in range(10)
