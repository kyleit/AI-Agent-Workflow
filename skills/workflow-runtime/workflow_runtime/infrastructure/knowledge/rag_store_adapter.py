"""RAG store adapter supporting SQLite FTS5, Qdrant REST vector search, and local RAG JSON index files."""
from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.ports.knowledge_ports import IRAGStorePort
from workflow_runtime.domain.knowledge.entities import RAGResult
from workflow_runtime.domain.workflow.value_objects import ArtifactPath
from workflow_runtime.shared.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RAGStoreAdapter(IRAGStorePort):
    """Adapter managing SQLite FTS5 index, Qdrant REST calls, and .agents/memory/rag/ index files."""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        qdrant_url: str = "http://localhost:6333",
        rag_dir: str | Path | None = None,
    ) -> None:
        self.db_path = str(db_path)
        self.qdrant_url = qdrant_url
        if rag_dir is None:
            self.rag_dir = Path(".agents/memory/rag")
        else:
            self.rag_dir = Path(rag_dir)

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_fts()
        self._load_local_rag_files()

    def _init_fts(self) -> None:
        """Initialize FTS5 virtual table if available, fallback to standard table if not."""
        try:
            with self._conn:
                self._conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                        entry_id UNINDEXED,
                        title,
                        content,
                        tags,
                        file_path
                    );
                """)
            self._has_fts = True
        except sqlite3.OperationalError as exc:
            logger.warning(f"SQLite FTS5 initialization failed, falling back to standard table: {exc}")
            self._has_fts = False
            with self._conn:
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_fts (
                        entry_id TEXT,
                        title TEXT,
                        content TEXT,
                        tags TEXT,
                        file_path TEXT
                    );
                """)

    def _load_local_rag_files(self) -> None:
        """Loads entries from .agents/memory/rag/ JSON files if present."""
        if not self.rag_dir.is_dir():
            logger.info(f"RAG index directory {self.rag_dir} not found. Skipping local indexing.")
            return

        for json_file in self.rag_dir.glob("*.json"):
            try:
                with json_file.open(encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    data_dict = cast(dict[str, Any], data)
                    raw_upsert = data_dict.get("upsert")
                    if isinstance(raw_upsert, list):
                        upsert_list = cast(list[Any], raw_upsert)
                        for item_raw in upsert_list:
                            if isinstance(item_raw, dict):
                                item = cast(dict[str, Any], item_raw)
                                item_id = str(item.get("id", ""))
                                text = str(item.get("text", ""))
                                raw_meta = item.get("metadata")
                                metadata = cast(dict[str, Any], raw_meta) if isinstance(raw_meta, dict) else {}
                                raw_tags = metadata.get("tags")
                                tags_list = cast(list[Any], raw_tags) if isinstance(raw_tags, list) else []
                                tags_str = " ".join(str(t) for t in tags_list)
                                title = item_id
                                self.index_document(
                                    relative_path=str(json_file),
                                    content=text,
                                    doc_metadata={"entry_id": item_id, "title": title, "tags": tags_str}
                                )
            except Exception as exc:
                logger.warning(f"Failed to parse RAG JSON file {json_file}: {exc}")

    def index_document(
        self, relative_path: str, content: str, doc_metadata: dict[str, Any] | None = None
    ) -> None:
        """Indexes a document record into the SQLite database."""
        meta = doc_metadata or {}
        entry_id = str(meta.get("entry_id", f"doc_{hash(relative_path) & 0xFFFFFFFF}"))
        title = str(meta.get("title", relative_path))
        tags = str(meta.get("tags", ""))
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO knowledge_fts (entry_id, title, content, tags, file_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entry_id, title, content, tags, relative_path),
            )

    def query_fts(self, query: str, limit: int = 5) -> list[RAGResult]:
        """Queries full-text search index."""
        if not query.strip():
            return []

        cursor = self._conn.cursor()
        results: list[RAGResult] = []

        if self._has_fts:
            try:
                safe_query = '"' + query.replace('"', '""') + '"'
                cursor.execute(
                    """
                    SELECT file_path, content, rank
                    FROM knowledge_fts
                    WHERE knowledge_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (safe_query, limit),
                )
                rows = cursor.fetchall()
                for row in rows:
                    raw_path = str(row["file_path"]) if row["file_path"] else "docs/memory.md"
                    rank_val = row["rank"]
                    score = abs(float(str(rank_val))) if rank_val is not None else 1.0
                    snippet = str(row["content"])[:200]
                    results.append(
                        RAGResult(
                            file_path=ArtifactPath(raw_path),
                            score=score,
                            snippet=snippet,
                            matched_lines=[1],
                        )
                    )
                if results:
                    return results
            except Exception as exc:
                logger.warning(f"FTS query failed: {exc}")

        try:
            like_pattern = f"%{query}%"
            cursor.execute(
                """
                SELECT file_path, content
                FROM knowledge_fts
                WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                LIMIT ?
                """,
                (like_pattern, like_pattern, like_pattern, limit),
            )
            rows = cursor.fetchall()
        except Exception as exc:
            logger.warning(f"LIKE fallback query failed: {exc}")
            rows = []
        for row in rows:
            raw_path = str(row["file_path"]) if row["file_path"] else "docs/memory.md"
            snippet = str(row["content"])[:200]
            results.append(
                RAGResult(
                    file_path=ArtifactPath(raw_path),
                    score=0.75,
                    snippet=snippet,
                    matched_lines=[1],
                )
            )

        return results

    def query_vector(self, query_text: str, limit: int = 5) -> list[dict[str, Any]]:
        """Queries Qdrant REST API with 1.0s timeout limit using scroll API to bypass embedding."""
        endpoint = f"{self.qdrant_url}/collections/ai-skill-framework/points/scroll"

        keywords = [w.strip() for w in query_text.split() if len(w.strip()) > 2]
        if not keywords:
            return []

        filter_conditions: list[dict[str, Any]] = []
        for kw in keywords:
            filter_conditions.append({
                "key": "text",
                "match": {"text": kw}
            })

        payload = json.dumps({
            "filter": {
                "should": filter_conditions
            },
            "limit": limit,
            "with_payload": True
        }).encode("utf-8")

        req = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    raw_body = json.loads(response.read().decode("utf-8"))
                    body = cast(dict[str, Any], raw_body) if isinstance(raw_body, dict) else {}
                    raw_res = body.get("result")
                    res_dict = cast(dict[str, Any], raw_res) if isinstance(raw_res, dict) else {}
                    raw_pts = res_dict.get("points")
                    pts_list = cast(list[dict[str, Any]], raw_pts) if isinstance(raw_pts, list) else []
                    return pts_list
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            logger.warning(f"Qdrant REST connection failed or timed out (1.0s): {exc}")

        return []

    def close(self) -> None:
        self._conn.close()


SQLiteStore = RAGStoreAdapter

__all__ = ["RAGStoreAdapter", "SQLiteStore"]
