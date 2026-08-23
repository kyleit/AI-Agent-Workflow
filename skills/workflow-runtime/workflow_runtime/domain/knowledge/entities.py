from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from workflow_runtime.domain.knowledge.value_objects import MemoryScope
from workflow_runtime.domain.workflow.value_objects import ArtifactPath


@dataclass
class MemoryEntry:
    entry_id: str
    title: str
    content: str
    tags: list[str]
    decay_score: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scope: MemoryScope = MemoryScope.PROJECT

    def is_relevant(self, tag: str) -> bool:
        return tag in self.tags

    def apply_decay(self, rate: float) -> MemoryEntry:
        new_score = max(0.0, self.decay_score * (1.0 - rate))
        self.decay_score = new_score
        return self


@dataclass
class RAGResult:
    file_path: ArtifactPath
    score: float
    snippet: str
    matched_lines: list[int]

    def is_high_confidence(self, threshold: float) -> bool:
        return self.score >= threshold


@dataclass
class KnowledgeGraph:
    nodes: dict[str, MemoryEntry] = field(default_factory=dict[str, MemoryEntry])
    edges: list[tuple[str, str, str]] = field(default_factory=list[tuple[str, str, str]])

    def add_node(self, entry: MemoryEntry) -> None:
        self.nodes[entry.entry_id] = entry

    def connect(self, source_id: str, target_id: str, relation: str) -> None:
        self.edges.append((source_id, target_id, relation))

    def query_related(self, entry_id: str) -> list[MemoryEntry]:
        related_ids: set[str] = set()
        for src, tgt, _ in self.edges:
            if src == entry_id:
                related_ids.add(tgt)
            elif tgt == entry_id:
                related_ids.add(src)
        return [self.nodes[nid] for nid in related_ids if nid in self.nodes]


__all__ = [
    "MemoryEntry",
    "RAGResult",
    "KnowledgeGraph",
]
