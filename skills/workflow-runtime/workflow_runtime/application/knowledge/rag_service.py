from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.ports.knowledge_ports import (
    IMemoryStorePort, IRAGStorePort)
from workflow_runtime.domain.knowledge.entities import RAGResult
from workflow_runtime.domain.workflow.value_objects import ArtifactPath
from workflow_runtime.shared.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RAGService:
    """Application service implementing RAG First policy multi-tier search pipeline."""

    def __init__(
        self,
        sqlite_store: IRAGStorePort,
        memory_store: IMemoryStorePort,
    ) -> None:
        self._sqlite_store = sqlite_store
        self._memory_store = memory_store

    def query(self, query: str, top_k: int = 5) -> list[RAGResult]:
        """Executes multi-tier search following RAG First priority hierarchy.

        Step 1: Attempt Level 2 Vector search via Qdrant adapter.
        Step 2: Fallback to Level 1 SQLite FTS5 / RAG index search.
        Step 3: Supplementary search across local Markdown docs if FTS yields 0 results.
        """
        results: list[RAGResult] = []

        query_vec_fn: Any = getattr(self._sqlite_store, "query_vector", None)
        if callable(query_vec_fn):
            raw_hits = query_vec_fn(query, limit=top_k)
            vector_hits = cast(list[Any], raw_hits) if isinstance(raw_hits, list) else []
            for hit in vector_hits:
                if isinstance(hit, dict):
                    hit_dict = cast(dict[str, Any], hit)
                    raw_payload = hit_dict.get("payload")
                    payload = cast(dict[str, Any], raw_payload) if isinstance(raw_payload, dict) else {}
                    file_path = str(payload.get("file_path", "docs/vector_result.md"))
                    score = float(str(hit_dict.get("score", 0.9)))
                    snippet = str(payload.get("text", ""))[:200]
                    results.append(
                        RAGResult(
                            file_path=ArtifactPath(file_path),
                            score=score,
                            snippet=snippet,
                            matched_lines=[1],
                        )
                    )

        if results:
            return results[:top_k]

        query_fts_fn: Any = getattr(self._sqlite_store, "query_fts", None)
        if callable(query_fts_fn):
            raw_fts = query_fts_fn(query, limit=top_k)
            fts_hits = cast(list[RAGResult], raw_fts) if isinstance(raw_fts, list) else []
            if fts_hits:
                return fts_hits[:top_k]

        md_matches = self._memory_store.search_markdown_files(query)
        for match_item in md_matches[:top_k]:
            if isinstance(match_item, dict):
                match = cast(dict[str, Any], match_item)
                results.append(
                    RAGResult(
                        file_path=ArtifactPath(str(match.get("path", ""))),
                        score=0.6,
                        snippet=str(match.get("snippet", "")),
                        matched_lines=[int(str(match.get("line_number", 1)))],
                    )
                )

        return results[:top_k]

    def search(self, query: str, top_k: int = 5) -> list[RAGResult]:
        """Alias for query."""
        return self.query(query, top_k)

    def index_document(
        self, file_path: str, title: str, content: str, tags: list[str] | None = None
    ) -> None:
        """Indexes a new document into RAG store."""
        tags_str = " ".join(tags) if tags else ""
        entry_id = f"doc_{hash(file_path + title) & 0xFFFFFFFF}"
        doc_metadata: dict[str, Any] = {
            "entry_id": entry_id,
            "title": title,
            "tags": tags_str,
        }
        self._sqlite_store.index_document(
            relative_path=file_path,
            content=content,
            doc_metadata=doc_metadata,
        )

    def get_context(self, query: str, top_k: int = 5) -> str:
        """Returns consolidated context text snippet from top RAG results."""
        results = self.query(query, top_k)
        if not results:
            return ""

        context_blocks: list[str] = []
        for idx, res in enumerate(results, start=1):
            path_str = res.file_path.path if hasattr(res.file_path, "path") else str(res.file_path)
            context_blocks.append(f"--- Context Block {idx} ({path_str}) ---\n{res.snippet}")

        return "\n\n".join(context_blocks)

    def search_by_tag(self, tag: str) -> list[RAGResult]:
        """Searches RAG store for items matching specific tag."""
        return self.query(query=tag)

    def extract_section(self, file_path: str, heading_title: str) -> str:
        """Extracts Markdown section content under a specific heading title."""
        path = Path(file_path)
        if not path.is_file():
            return ""

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to read file {file_path}: {exc}")
            return ""

        lines = content.splitlines()
        capturing = False
        target_heading = heading_title.lower().strip("# ").strip()
        extracted_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                current_heading = stripped.strip("# ").lower().strip()
                if current_heading == target_heading:
                    capturing = True
                    extracted_lines.append(line)
                    continue
                elif capturing:
                    break

            if capturing:
                extracted_lines.append(line)

        return "\n".join(extracted_lines)


__all__ = ["RAGService"]
