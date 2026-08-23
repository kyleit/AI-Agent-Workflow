from __future__ import annotations

from typing import Any

from workflow_runtime.domain.entities.patch import ASTPatchPayload
from workflow_runtime.domain.interfaces.broadcaster import IHMRBroadcaster
from workflow_runtime.domain.services.ast_differ import ASTDifferService


class ProcessFileChangeUseCase:
    def __init__(self, broadcaster: IHMRBroadcaster, differ: ASTDifferService) -> None:
        self.broadcaster = broadcaster
        self.differ = differ
        self.current_version = 1

    async def execute(self, old_ast: Any, new_ast: Any, doc_path: str) -> None:
        patches = self.differ.diff_ast(old_ast, new_ast)
        if not patches:
            return

        payload = ASTPatchPayload(
            base_version=self.current_version,
            target_version=self.current_version + 1,
            patches=patches
        )
        self.current_version += 1

        envelope = {
            "version": "1.0",
            "type": "AST_PATCH_EVENT",
            "timestamp": 0,
            "payload": payload.__dict__
        }
        await self.broadcaster.broadcast(envelope)


__all__ = ["ProcessFileChangeUseCase"]
