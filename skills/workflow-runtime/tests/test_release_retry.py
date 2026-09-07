from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.aiwf_release import engine


def test_resume_candidate_when_version_bump_was_already_written(tmp_path: Path) -> None:
    (tmp_path / "MANIFEST.json").write_text(json.dumps({"version": "2.0.1"}), encoding="utf-8")
    (tmp_path / ".agents" / "state" / "release").mkdir(parents=True)
    (tmp_path / ".agents" / "state" / "release" / "2.0.1.json").write_text(
        json.dumps({"version": "2.0.1", "previous_version": "2.0.0", "bump_part": "patch", "steps": []}),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    cfg = {"version": {"source_of_truth": "MANIFEST.json#version", "strategy": "auto-conventional", "files": ["MANIFEST.json#version"]}, "receipt_dir": ".agents/state/release"}

    plan = engine._resume_or_compute(tmp_path, cfg, None)

    assert plan["resumed"] is True
    assert plan["next"] == "2.0.1"
    assert plan["current"] == "2.0.0"
