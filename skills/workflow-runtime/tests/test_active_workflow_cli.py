import argparse
import json
from unittest.mock import patch
from workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing import (
    _normalize_active_workflow,
    do_active_workflow,
    do_workflow,
)


def test_normalize_active_workflow_string():
    session = {
        "active_workflow": "FIX-029_seamless_git_push_gate",
        "active_phase": "implementation",
        "suggested_next_skill": "quick-fix",
        "status": "in_progress",
        "checkpoint": 6,
    }
    normalized = _normalize_active_workflow("FIX-029_seamless_git_push_gate", session)
    assert normalized is not None
    assert normalized["workflow_id"] == "FIX-029_seamless_git_push_gate"
    assert normalized["current_phase"] == "implementation"
    assert normalized["next_step"] == "quick-fix"


def test_normalize_active_workflow_dict():
    session = {}
    active_dict = {
        "workflow_id": "WF-001",
        "current_phase": "blueprint",
        "next_step": "plan-to-blueprint",
        "status": "running",
        "checkpoint": 4,
    }
    normalized = _normalize_active_workflow(active_dict, session)
    assert normalized is not None
    assert normalized["workflow_id"] == "WF-001"
    assert normalized["current_phase"] == "blueprint"
    assert normalized["next_step"] == "plan-to-blueprint"


def test_do_active_workflow_string_text(capsys):
    session = {
        "active_workflow": "FIX-029_seamless_git_push_gate",
        "active_phase": "implementation",
        "suggested_next_skill": "quick-fix",
    }
    args = argparse.Namespace(json=False)
    with patch("workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing.load_session", return_value=session):
        ret = do_active_workflow(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "Workflow ID: FIX-029_seamless_git_push_gate" in out
    assert "Current Phase: implementation" in out


def test_do_active_workflow_string_json(capsys):
    session = {
        "active_workflow": "FIX-029_seamless_git_push_gate",
        "active_phase": "implementation",
        "suggested_next_skill": "quick-fix",
        "status": "in_progress",
        "checkpoint": 6,
    }
    args = argparse.Namespace(json=True)
    with patch("workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing.load_session", return_value=session):
        ret = do_active_workflow(args)
    assert ret == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["active"] is True
    assert data["workflow_id"] == "FIX-029_seamless_git_push_gate"
    assert data["current_phase"] == "implementation"
    assert data["next_step"] == "quick-fix"


def test_do_active_workflow_none_json(capsys):
    session = {}
    args = argparse.Namespace(json=True)
    with patch("workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing.load_session", return_value=session), \
         patch("os.path.exists", return_value=False):
        ret = do_active_workflow(args)
    assert ret == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["active"] is False
    assert data["workflow_id"] is None