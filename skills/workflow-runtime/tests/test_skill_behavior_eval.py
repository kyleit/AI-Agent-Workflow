from __future__ import annotations

import json
from pathlib import Path

from workflow_runtime.application.verification.skill_behavior_eval import (
    SkillBehaviorEvalService,
)


def test_behavior_eval_enforces_required_and_forbidden_patterns(tmp_path: Path) -> None:
    evals = tmp_path / "evals"
    evals.mkdir()
    (evals / "approval.json").write_text(json.dumps({
        "scenarios": [{
            "scenario_id": "approval",
            "response_fixture": "PROMPT_UNAVAILABLE; one bound fallback",
            "required_patterns": [{"name": "explicit", "pattern": "PROMPT_UNAVAILABLE"}],
            "forbidden_patterns": [{"name": "magic", "pattern": "magic phrase"}],
        }]
    }), encoding="utf-8")

    result = SkillBehaviorEvalService().evaluate_skill(tmp_path)

    assert result.passed is True
    assert result.score == 100
    assert result.assertions_evaluated == 2


def test_behavior_eval_reports_missing_required_pattern(tmp_path: Path) -> None:
    evals = tmp_path / "evals"
    evals.mkdir()
    (evals / "broken.json").write_text(json.dumps({
        "scenarios": [{
            "scenario_id": "broken",
            "response_fixture": "blocked",
            "required_patterns": [{"name": "missing", "pattern": "PASS"}],
        }]
    }), encoding="utf-8")

    result = SkillBehaviorEvalService().evaluate_skill(tmp_path)

    assert result.passed is False
    assert "broken:missing: required pattern missing" in result.failures
