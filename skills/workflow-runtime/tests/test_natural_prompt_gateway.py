import json
import os

from workflow_runtime.application.workflow.workflow_entry_gateway import WorkflowEntryGateway


def test_plain_vietnamese_prompt_routes_into_aiwf_workflow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agents" / "state").mkdir(parents=True)

    gateway = WorkflowEntryGateway(str(tmp_path))
    result = gateway.handle_request("sửa toàn bộ lệnh cli cho đúng")

    assert result["status"] == "ROUTED"
    assert result["intent"] == "bug_fix"
    assert result["execution_mode"] == "workflow"
    assert result["current_phase"] == "brainstorming"
    assert result["next_skill"] == "quick-fix"
    assert os.environ["AIWF_WORKFLOW_ID"] == result["workflow_id"]
    assert os.environ["AIWF_EXECUTION_MODE"] == "workflow"

    workflow_path = tmp_path / ".agents" / "state" / "workflow.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    assert workflow["status"] == "IN_PROGRESS"
    assert workflow["suggested_next_skill"] == "quick-fix"

    events_path = tmp_path / ".agents" / "state" / "events" / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    event_types = [event["event_type"] for event in events]
    assert "workflow.request.received" in event_types
    assert "workflow.started" in event_types
    assert "skill.selected" in event_types


def test_plain_ambiguous_prompt_fails_closed_into_workflow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agents" / "state").mkdir(parents=True)

    gateway = WorkflowEntryGateway(str(tmp_path))
    result = gateway.handle_request("làm giúp tôi phần này cho ổn hơn")

    assert result["status"] == "ROUTED"
    assert result["intent"] == "natural_workflow_request"
    assert result["next_skill"] == "brainstorming"
