import pytest
from unittest.mock import MagicMock
from workflow_runtime.application.workflow.coordinator_service import WorkflowCoordinatorService, TickResult
from workflow_runtime.domain.workflow.entities import WorkflowState
from workflow_runtime.domain.workflow.value_objects import PhaseStatus

def test_coordinator_tick_brainstorming():
    # Setup mocks
    mock_repo = MagicMock()
    mock_phase_svc = MagicMock()
    mock_gate_svc = MagicMock()

    # Create dummy state
    dummy_state = WorkflowState(
        session_id="test_session",
        active_phase="brainstorming",
        checkpoint=1,
        status=PhaseStatus.IN_PROGRESS,
        started_at=None,
        updated_at=None
    )
    mock_repo.get_state.return_value = dummy_state
    
    coordinator = WorkflowCoordinatorService(mock_repo, mock_phase_svc, mock_gate_svc)
    
    # Execute tick
    result = coordinator.tick(dry_run=False, session_id="test_session")
    
    # Verify
    assert result.session_id == "test_session"
    assert result.active_phase == "brainstorming"
    assert result.status == "IN_PROGRESS"
    assert result.requires_user_input == False
    mock_repo.save_state.assert_called_once()
