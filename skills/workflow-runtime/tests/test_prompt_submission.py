import os
import pytest
import json
from workflow_entry_gateway import WorkflowEntryGateway
from state_store import get_state_store, get_active_work_item_id

def test_prompt_submission_validation(isolated_workspace):
    gateway = WorkflowEntryGateway(isolated_workspace)
    
    # Empty prompt should raise ValueError
    with pytest.raises(ValueError, match="request_text cannot be empty"):
        gateway.handle_request("")
        
    with pytest.raises(ValueError, match="request_text cannot be empty"):
        gateway.handle_request("   ")

def test_prompt_submission_creates_workflow(isolated_workspace):
    gateway = WorkflowEntryGateway(isolated_workspace)
    
    # Submit prompt-only feature request
    res = gateway.handle_request("Implement FEAT-999 auto workflow")
    
    assert res["status"] == "ROUTED"
    assert res["workflow_id"] == "FEAT-999"
    assert res["intent"] == "feature_request"
    
    # Check that work item was registered
    active_id = get_active_work_item_id()
    assert active_id == "FEAT-999"
    
    # Check that files were created
    store = get_state_store()
    wf = store.get("workflow")
    assert wf is not None
    assert wf.get("active_workflow") == "standard-development"
