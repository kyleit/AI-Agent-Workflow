# test_skill_migration.py
import pytest
import os
import sys
import warnings

# Add script directory to sys.path to find skill_migration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from skill_migration import SkillManifestV3, validate_skill_manifest, SkillValidationError, LegacySkillAdapter
from websocket_server import RuntimeAPIServer
from runtime_sdk import RuntimeSDKv3

def test_manifest_validation_success():
    valid_manifest = {
        "skill_id": "initialize-workflow",
        "version": "3.0.0",
        "capabilities": ["initialization"],
        "required_permissions": ["workspace.write"],
        "input_schema": {},
        "output_schema": {},
        "tool_requirements": [],
        "runtime_requirements": {}
    }
    manifest = validate_skill_manifest(valid_manifest)
    assert manifest.skill_id == "initialize-workflow"
    assert manifest.version == "3.0.0"

def test_manifest_validation_failure():
    invalid_manifest = {
        "skill_id": "initialize-workflow",
        # Missing version
        "capabilities": ["initialization"],
        "required_permissions": ["workspace.write"],
        "input_schema": {},
        "output_schema": {},
        "tool_requirements": [],
        "runtime_requirements": {}
    }
    with pytest.raises(SkillValidationError):
        validate_skill_manifest(invalid_manifest)

@pytest.mark.asyncio
async def test_legacy_skill_adapter():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    await sdk.create_session("session-test")
    
    adapter = LegacySkillAdapter(skill_id="legacy-brainstorming", sdk_v3=sdk)
    
    with pytest.deprecated_call():
        res = await adapter.execute_legacy_flow(
            session_id="session-test",
            task_id="task-123",
            payload={}
        )
        assert res["status"] == "success"
        assert res["legacy_output"] == "migrated_execution_complete"
        
    # Check event emission
    events = await sdk.get_session_events("session-test")
    topics = [e["topic"] for e in events]
    assert "task.queued" in topics
    assert "skill.execution_completed" in topics
