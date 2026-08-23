from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from workflow_runtime.application.dtos.snapshot_dtos import (
    SaveSnapshotRequestDTO, SessionSnapshotDTO)
from workflow_runtime.application.use_cases.snapshot_use_cases import (
    RestoreSnapshotUseCase, SaveSnapshotUseCase)
from workflow_runtime.infrastructure.persistence.snapshot_repository_impl import \
    InMemorySnapshotRepository

router = APIRouter(prefix="/api/v1/vir/snapshots", tags=["snapshots"])

_global_snapshot_repo = InMemorySnapshotRepository()

def get_snapshot_repository() -> InMemorySnapshotRepository:
    return _global_snapshot_repo

def get_save_snapshot_use_case(
    repo: InMemorySnapshotRepository = Depends(get_snapshot_repository)
) -> SaveSnapshotUseCase:
    return SaveSnapshotUseCase(repo)

def get_restore_snapshot_use_case(
    repo: InMemorySnapshotRepository = Depends(get_snapshot_repository)
) -> RestoreSnapshotUseCase:
    return RestoreSnapshotUseCase(repo)

@router.post("", response_model=SessionSnapshotDTO, status_code=status.HTTP_201_CREATED)
async def save_snapshot(
    payload: SaveSnapshotRequestDTO,
    use_case: SaveSnapshotUseCase = Depends(get_save_snapshot_use_case)
) -> SessionSnapshotDTO:
    """Saves session state snapshot into ring buffer."""
    try:
        return use_case.execute(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/rollback", response_model=SessionSnapshotDTO)
async def rollback_snapshot(
    session_id: str,
    snapshot_id: Optional[str] = None,
    use_case: RestoreSnapshotUseCase = Depends(get_restore_snapshot_use_case)
) -> SessionSnapshotDTO:
    """Restores session state to specified snapshot or latest clean version."""
    try:
        return use_case.execute(session_id=session_id, snapshot_id=snapshot_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
