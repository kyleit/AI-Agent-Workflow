from fastapi import FastAPI
from fastapi.testclient import TestClient

from workflow_runtime.presentation.api.snapshot_router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_tc303_snapshot_router_api():
    """TC-303-PY: Assert POST /api/v1/vir/snapshots/rollback returns HTTP 200 with last clean snapshot."""
    session_id = "test_router_session"

    save_payload = {
        "session_id": session_id,
        "ast_schema_json": '{"nodes": ["N1", "N2"]}',
        "state_payload": {"formValues": {"N1": {"input_1": "test_value"}}},
        "trigger_reason": "hmr_update"
    }

    response = client.post("/api/v1/vir/snapshots", json=save_payload)
    assert response.status_code == 201
    dto = response.json()
    assert dto["session_id"] == session_id
    assert dto["ast_schema_json"] == '{"nodes": ["N1", "N2"]}'
    snapshot_id = dto["snapshot_id"]

    rollback_response = client.post(
        f"/api/v1/vir/snapshots/rollback?session_id={session_id}"
    )
    assert rollback_response.status_code == 200
    rollback_dto = rollback_response.json()
    assert rollback_dto["snapshot_id"] == snapshot_id
    assert rollback_dto["session_id"] == session_id

def test_snapshot_router_error_handling():
    """Test 404 error response when rolling back a non-existent session."""
    rollback_response = client.post(
        "/api/v1/vir/snapshots/rollback?session_id=non_existent_session"
    )
    assert rollback_response.status_code == 404
    assert "not found" in rollback_response.json()["detail"].lower()
