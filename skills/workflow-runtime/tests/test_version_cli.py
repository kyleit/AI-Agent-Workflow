from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_version_aliases_report_framework_version() -> None:
    package_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_root)
    for argument in ("--version", "version"):
        result = subprocess.run(
            [sys.executable, "-m", "workflow_runtime", argument],
            cwd=package_root.parent.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip().startswith("aiwf ")
        assert result.stdout.strip() != "aiwf 0.0.0"

