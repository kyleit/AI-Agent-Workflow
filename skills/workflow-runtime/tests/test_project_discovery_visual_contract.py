from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_runtime.application.system.project_discovery import (
    build_visual_contract,
)

pytestmark = pytest.mark.unit


def test_frontend_discovery_publishes_mobile_first_contract():
    contract = build_visual_contract(["React"])

    assert contract["required"] is True
    assert contract["e2e_required"] is True
    assert contract["mode"] == "real-browser"
    assert contract["viewport_order"] == ["mobile", "desktop", "tablet"]
    assert contract["viewports"] == {
        "mobile": [375, 390],
        "desktop": [1440, 1920],
        "tablet": [768, 820],
    }


def test_non_frontend_does_not_require_visual_e2e():
    contract = build_visual_contract([])

    assert contract["required"] is False
    assert contract["e2e_required"] is False
