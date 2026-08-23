from typing import Any, Dict

from pydantic import BaseModel, Field


class SaveSnapshotRequestDTO(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    ast_schema_json: str = Field(..., description="Current AST JSON string")
    state_payload: Dict[str, Any] = Field(..., description="Serialized SessionState dictionary")
    trigger_reason: str = Field("hmr_update", description="Reason for snapshot creation")

class SessionSnapshotDTO(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: float = Field(..., description="Timestamp of snapshot creation")
    ast_schema_json: str = Field(..., description="AST JSON string")
    state_payload: Dict[str, Any] = Field(..., description="Serialized state payload")
    trigger_reason: str = Field(..., description="Reason for snapshot creation")
