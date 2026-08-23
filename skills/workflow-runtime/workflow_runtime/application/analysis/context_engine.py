# context_engine.py
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, cast


class StateConflictError(Exception):
    pass


class SharedSessionContext:
    def __init__(
        self,
        context_id: str,
        session_id: str,
        version: int = 1,
        content_refs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        parent_version: int | None = None,
        created_by: str = "system"
    ) -> None:
        self.context_id = context_id
        self.session_id = session_id
        self.version = version
        self.created_at = datetime.now().astimezone().isoformat()
        self.updated_at = self.created_at
        self.content_refs: dict[str, Any] = copy.deepcopy(content_refs or {})
        self.metadata: dict[str, Any] = copy.deepcopy(metadata or {})
        self.parent_version = parent_version
        self.created_by = created_by
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        serialized = json.dumps(
            {"content_refs": self.content_refs, "metadata": self.metadata, "version": self.version},
            sort_keys=True
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "session_id": self.session_id,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "content_refs": self.content_refs,
            "metadata": self.metadata,
            "parent_version": self.parent_version,
            "created_by": self.created_by,
            "hash": self.hash
        }


class AgentContextDelta:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.local_changes: dict[str, Any] = {}
        self.local_decisions: list[Any] = []
        self.scratch_data: dict[str, Any] = {}
        self.evidence_references: list[Any] = []
        self.output_summaries = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "local_changes": self.local_changes,
            "local_decisions": self.local_decisions,
            "scratch_data": self.scratch_data,
            "evidence_references": self.evidence_references,
            "output_summaries": self.output_summaries
        }


class SharedContextEngine:
    def __init__(
        self,
        session_id: str,
        initial_content: dict[str, Any] | None = None,
        event_store: Any = None
    ) -> None:
        self.session_id = session_id
        self.event_store = event_store

        context_id = str(uuid.uuid4())
        self.revision = 1
        first_ctx = SharedSessionContext(
            context_id=context_id,
            session_id=session_id,
            version=1,
            content_refs=initial_content
        )

        self._snapshots: dict[int, SharedSessionContext] = {1: first_ctx}
        self._lock = asyncio.Lock()

        if self.event_store is not None:
            append_fn: Any = getattr(self.event_store, "append_event", None)
            if callable(append_fn):
                append_fn(
                    session_id=self.session_id,
                    topic="context.created",
                    payload=first_ctx.to_dict()
                )

    async def get_context_slice(self, read_keys: list[str]) -> dict[str, Any]:
        async with self._lock:
            current_ctx = self._snapshots[self.revision]

            slice_data: dict[str, Any] = {}
            for key in read_keys:
                if key in current_ctx.content_refs:
                    slice_data[key] = copy.deepcopy(current_ctx.content_refs[key])
            return {
                "revision": self.revision,
                "data": slice_data,
                "hash": current_ctx.hash
            }

    async def get_snapshot(self, version: int) -> SharedSessionContext | None:
        async with self._lock:
            return self._snapshots.get(version)

    async def merge_delta(
        self,
        base_revision: int,
        delta: dict[str, Any],
        agent_id: str = "system",
        expected_hash: str | None = None
    ) -> int:
        async with self._lock:
            current_ctx = self._snapshots[self.revision]

            append_fn: Any = getattr(self.event_store, "append_event", None) if self.event_store is not None else None

            if callable(append_fn):
                append_fn(
                    session_id=self.session_id,
                    topic="context.merge_requested",
                    payload={"agent_id": agent_id, "base_revision": base_revision, "delta": delta}
                )

            if base_revision != self.revision:
                if callable(append_fn):
                    append_fn(
                        session_id=self.session_id,
                        topic="context.merge_rejected",
                        payload={"reason": "stale context version", "agent_id": agent_id}
                    )
                raise StateConflictError(
                    f"Conflict detected. Base revision {base_revision} does not match current revision {self.revision}."
                )

            if expected_hash and expected_hash != current_ctx.hash:
                if callable(append_fn):
                    append_fn(
                        session_id=self.session_id,
                        topic="context.merge_rejected",
                        payload={"reason": "hash validation failure", "agent_id": agent_id}
                    )
                raise StateConflictError("Hash validation failure. State has modified in unexpected ways.")

            new_content = copy.deepcopy(current_ctx.content_refs)
            for key, val in delta.items():
                if isinstance(val, dict) and key in new_content and isinstance(new_content[key], dict):
                    target_dict = cast(dict[str, Any], new_content[key])
                    val_dict = cast(dict[str, Any], val)
                    target_dict.update(copy.deepcopy(val_dict))
                else:
                    new_content[key] = copy.deepcopy(cast(Any, val))

            new_version = self.revision + 1
            new_ctx = SharedSessionContext(
                context_id=str(uuid.uuid4()),
                session_id=self.session_id,
                version=new_version,
                content_refs=new_content,
                parent_version=self.revision,
                created_by=agent_id
            )

            self._snapshots[new_version] = new_ctx
            self.revision = new_version

            if callable(append_fn):
                append_fn(
                    session_id=self.session_id,
                    topic="context.snapshot_created",
                    payload=new_ctx.to_dict()
                )
                append_fn(
                    session_id=self.session_id,
                    topic="context.version_updated",
                    payload={"new_version": new_version}
                )

            return new_version

    async def get_full_context(self) -> dict[str, Any]:
        async with self._lock:
            return copy.deepcopy(self._snapshots[self.revision].content_refs)

    def lazy_load_reference(self, reference_uri: str) -> dict[str, Any]:
        return {"reference_uri": reference_uri, "status": "lazy_loaded"}

    def compact_context(self) -> None:
        if len(self._snapshots) > 4:
            keys = sorted(list(self._snapshots.keys()))
            for k in keys[1:-3]:
                self._snapshots[k].content_refs = {}


__all__ = [
    "StateConflictError",
    "SharedSessionContext",
    "AgentContextDelta",
    "SharedContextEngine",
]
