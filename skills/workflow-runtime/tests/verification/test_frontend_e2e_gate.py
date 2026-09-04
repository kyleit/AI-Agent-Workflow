from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workflow_runtime.application.verification.frontend_e2e_gate import (
    REQUIRED_VIEWPORT_ORDER,
    REQUIRED_WIDTHS,
    FrontendGateResult,
    load_visual_manifest,
    validate_frontend_evidence,
)

pytestmark = pytest.mark.unit


def _manifest(**overrides: object) -> dict[str, object]:
    screenshot_hashes = [
        {"family": family, "width": width, "path": f"{family}-{width}.png", "sha256": "a" * 64}
        for family, widths in REQUIRED_WIDTHS.items()
        for width in widths
    ]
    layout_assertions = [
        {"family": family, "width": width, "passed": True}
        for family, widths in REQUIRED_WIDTHS.items()
        for width in widths
    ]
    manifest: dict[str, object] = {
        "browser_evidence": True,
        "adapter": "playwright",
        "viewport_order": list(REQUIRED_VIEWPORT_ORDER),
        "viewports": {key: list(value) for key, value in REQUIRED_WIDTHS.items()},
        "iterations": [
            {
                "number": 2,
                "sequence": ["automation", "screenshot", "validate", "fix", "rerun"],
                "screenshot_hashes": screenshot_hashes,
                "layout_assertions": layout_assertions,
                "interactions": [{"action": "navigate"}],
                "findings": [],
                "layout_assertions": layout_assertions,
                "interactions": [{"action": "navigate"}],
            }
        ],
        "unresolved_findings": [],
        "console_errors": [],
        "network_errors": [],
        "decision": "PASS",
    }
    manifest.update(overrides)
    return manifest


def test_clean_real_browser_manifest_passes():
    result = validate_frontend_evidence(_manifest())

    assert isinstance(result, FrontendGateResult)
    assert result.ok is True
    assert result.reason == "frontend_visual_pass"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("browser_evidence", False, "frontend_browser_evidence_missing"),
        ("adapter", "stub", "frontend_mock_evidence_forbidden"),
        ("viewport_order", ["desktop", "mobile", "tablet"], "frontend_viewport_order_invalid"),
        ("console_errors", ["page error"], "frontend_runtime_errors_present"),
        ("decision", "BLOCKED", "frontend_visual_pass_missing"),
    ],
)
def test_invalid_evidence_is_blocked(field: str, value: object, reason: str):
    result = validate_frontend_evidence(_manifest(**{field: value}))

    assert result.ok is False
    assert result.reason == reason


def test_each_required_width_and_rerun_are_required():
    missing_widths = _manifest(viewports={"mobile": [375, 390], "desktop": [1440], "tablet": [768, 820]})
    no_rerun = _manifest(
        iterations=[
            {
                "number": 1,
                "sequence": ["automation", "screenshot", "validate"],
                "screenshots": ["all.png"],
                "findings": [{"kind": "overflow"}],
            },
            {
                "number": 2,
                "sequence": ["automation", "screenshot", "validate"],
                "screenshot_hashes": [],
                "findings": [],
            },
        ]
    )

    assert validate_frontend_evidence(missing_widths).reason == "frontend_viewport_missing:desktop"
    assert validate_frontend_evidence(no_rerun).reason == "frontend_rerun_after_fix_missing"


def test_manifest_loader_is_workspace_scoped(tmp_path):
    path = tmp_path / "docs" / "aiwf-runs" / "FEAT-1" / "08-visual" / "frontend-e2e.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_manifest()), encoding="utf-8")

    loaded = load_visual_manifest("FEAT-1", workspace_root=tmp_path)

    assert loaded["decision"] == "PASS"
