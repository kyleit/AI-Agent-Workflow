import pytest

from workflow_runtime.application.dtos.snapshot_dtos import (
    SaveSnapshotRequestDTO, SessionSnapshotDTO)
from workflow_runtime.application.use_cases.snapshot_use_cases import (
    RestoreSnapshotUseCase, SaveSnapshotUseCase)
from workflow_runtime.infrastructure.persistence.snapshot_repository_impl import \
    InMemorySnapshotRepository


def test_tc302_save_and_restore_snapshot_use_cases():
    """TC-302-PY: Assert SaveSnapshotUseCase persists DTO payload and returns valid SessionSnapshotDTO."""
    repo = InMemorySnapshotRepository()
    save_use_case = SaveSnapshotUseCase(repo)
    restore_use_case = RestoreSnapshotUseCase(repo)

    session_id = "test_session_use_cases"
    request = SaveSnapshotRequestDTO(
        session_id=session_id,
        ast_schema_json='{"rootNode": "Node_1"}',
        state_payload={"formValues": {"node_1": {"field_a": "hello"}}},
        trigger_reason="hmr_update"
    )

    dto = save_use_case.execute(request)
    assert isinstance(dto, SessionSnapshotDTO)
    assert dto.session_id == session_id
    assert dto.ast_schema_json == '{"rootNode": "Node_1"}'
    assert dto.state_payload == {"formValues": {"node_1": {"field_a": "hello"}}}
    assert dto.snapshot_id.startswith("snap_")

    restored_dto = restore_use_case.execute(session_id=session_id)
    assert restored_dto.snapshot_id == dto.snapshot_id
    assert restored_dto.ast_schema_json == dto.ast_schema_json

    restored_by_id = restore_use_case.execute(session_id=session_id, snapshot_id=dto.snapshot_id)
    assert restored_by_id.snapshot_id == dto.snapshot_id

def test_restore_snapshot_not_found_errors():
    """Assert ValueError when session or snapshot ID is invalid."""
    repo = InMemorySnapshotRepository()
    restore_use_case = RestoreSnapshotUseCase(repo)

    with pytest.raises(ValueError, match="Session with ID 'invalid_session' not found"):
        restore_use_case.execute("invalid_session")

    save_use_case = SaveSnapshotUseCase(repo)
    save_use_case.execute(SaveSnapshotRequestDTO(
        session_id="session_exist",
        ast_schema_json="{}",
        state_payload={}
    ))

    with pytest.raises(ValueError, match="Snapshot with ID 'snap_missing' not found"):
        restore_use_case.execute("session_exist", snapshot_id="snap_missing")
