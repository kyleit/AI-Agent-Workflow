# context_engine.py
import copy
import asyncio
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from event_store import SQLiteEventStore

class StateConflictError(Exception):
    pass

class SharedSessionContext:
    def __init__(
        self,
        context_id: str,
        session_id: str,
        version: int = 1,
        content_refs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_version: Optional[int] = None,
        created_by: str = "system"
    ) -> None:
        self.context_id = context_id
        self.session_id = session_id
        self.version = version
        self.created_at = datetime.now().astimezone().isoformat()
        self.updated_at = self.created_at
        self.content_refs = copy.deepcopy(content_refs or {})
        self.metadata = copy.deepcopy(metadata or {})
        self.parent_version = parent_version
        self.created_by = created_by
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        serialized = json.dumps(
            {"content_refs": self.content_refs, "metadata": self.metadata, "version": self.version},
            sort_keys=True
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
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
        self.local_changes = {}
        self.local_decisions = []
        self.scratch_data = {}
        self.evidence_references = []
        self.output_summaries = ""

    def to_dict(self) -> Dict[str, Any]:
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
        initial_content: Optional[Dict[str, Any]] = None,
        event_store: Optional[SQLiteEventStore] = None
    ) -> None:
        self.session_id = session_id
        self.event_store = event_store
        
        # Init first context snapshot
        context_id = str(uuid.uuid4())
        self.revision = 1
        first_ctx = SharedSessionContext(
            context_id=context_id,
            session_id=session_id,
            version=1,
            content_refs=initial_content
        )
        
        # Snapshot mapping (immutable snapshots tracking)
        self._snapshots: Dict[int, SharedSessionContext] = {1: first_ctx}
        self._lock = asyncio.Lock()
        
        if self.event_store:
            self.event_store.append_event(
                session_id=self.session_id,
                topic="context.created",
                payload=first_ctx.to_dict()
            )

    async def get_context_slice(self, read_keys: List[str]) -> Dict[str, Any]:
        async with self._lock:
            current_ctx = self._snapshots[self.revision]
            
            # Copy-on-Write slice of shared references
            slice_data = {}
            for key in read_keys:
                if key in current_ctx.content_refs:
                    slice_data[key] = copy.deepcopy(current_ctx.content_refs[key])
            return {
                "revision": self.revision,
                "data": slice_data,
                "hash": current_ctx.hash
            }

    async def get_snapshot(self, version: int) -> Optional[SharedSessionContext]:
        async with self._lock:
            return self._snapshots.get(version)

    async def merge_delta(
        self,
        base_revision: int,
        delta: Dict[str, Any],
        agent_id: str = "system",
        expected_hash: Optional[str] = None
    ) -> int:
        async with self._lock:
            current_ctx = self._snapshots[self.revision]
            
            # Trigger event request
            if self.event_store:
                self.event_store.append_event(
                    session_id=self.session_id,
                    topic="context.merge_requested",
                    payload={"agent_id": agent_id, "base_revision": base_revision, "delta": delta}
                )

            # Optimistic Concurrency Control (OCC) & Hash checks
            if base_revision != self.revision:
                if self.event_store:
                    self.event_store.append_event(
                        session_id=self.session_id,
                        topic="context.merge_rejected",
                        payload={"reason": "stale context version", "agent_id": agent_id}
                    )
                raise StateConflictError(
                    f"Conflict detected. Base revision {base_revision} does not match current revision {self.revision}."
                )

            if expected_hash and expected_hash != current_ctx.hash:
                if self.event_store:
                    self.event_store.append_event(
                        session_id=self.session_id,
                        topic="context.merge_rejected",
                        payload={"reason": "hash validation failure", "agent_id": agent_id}
                    )
                raise StateConflictError("Hash validation failure. State has modified in unexpected ways.")

            # Construct new context based on Cow Strategy (Do not modify existing)
            new_content = copy.deepcopy(current_ctx.content_refs)
            for key, val in delta.items():
                if isinstance(val, dict) and key in new_content and isinstance(new_content[key], dict):
                    new_content[key].update(copy.deepcopy(val))
                else:
                    new_content[key] = copy.deepcopy(val)
            
            new_version = self.revision + 1
            new_ctx = SharedSessionContext(
                context_id=str(uuid.uuid4()),
                session_id=self.session_id,
                version=new_version,
                content_refs=new_content,
                parent_version=self.revision,
                created_by=agent_id
            )
            
            # Record immutable snapshot
            self._snapshots[new_version] = new_ctx
            self.revision = new_version
            
            if self.event_store:
                self.event_store.append_event(
                    session_id=self.session_id,
                    topic="context.snapshot_created",
                    payload=new_ctx.to_dict()
                )
                self.event_store.append_event(
                    session_id=self.session_id,
                    topic="context.version_updated",
                    payload={"new_version": new_version}
                )
                
            return new_version

    async def get_full_context(self) -> Dict[str, Any]:
        async with self._lock:
            return copy.deepcopy(self._snapshots[self.revision].content_refs)

    # Extension Points for Optimization & Memory boundary (FR-06 & FR-07)
    def lazy_load_reference(self, reference_uri: str) -> Dict[str, Any]:
        # Lazy loading extension point
        return {"reference_uri": reference_uri, "status": "lazy_loaded"}

    def compact_context(self) -> None:
        # Context compaction extension point to evict older versions memory consumption
        # Keep version 1 (base) and the last 3 versions
        if len(self._snapshots) > 4:
            keys = sorted(list(self._snapshots.keys()))
            for k in keys[1:-3]:
                # Evict middle snapshots references but keep shell dict to preserve DAG
                self._snapshots[k].content_refs = {}
