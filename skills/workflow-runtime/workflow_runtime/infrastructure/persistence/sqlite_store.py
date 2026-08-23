"""Persistent SQLite store adapter using standard library sqlite3."""

import json
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow_runtime.domain.knowledge.entities import RAGResult
from workflow_runtime.domain.workflow.entities import Checkpoint, WorkflowState
from workflow_runtime.domain.workflow.repositories import IWorkflowRepository
from workflow_runtime.domain.workflow.value_objects import (ArtifactPath,
                                                            PhaseStatus,
                                                            RoleId)
from workflow_runtime.shared.errors import EntityNotFoundError
from workflow_runtime.shared.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class SQLiteStore(IWorkflowRepository):
    """SQLite implementation of IWorkflowRepository using raw sqlite3, supporting FTS5 and Qdrant REST."""

    def __init__(self, db_path: str = ":memory:", qdrant_url: str = "http://localhost:6333") -> None:
        self._db_path = str(db_path)
        self.qdrant_url = qdrant_url
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        """Initializes database tables if they do not exist."""
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_states (
                    session_id TEXT PRIMARY KEY,
                    active_phase TEXT NOT NULL,
                    checkpoint INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,
                    validated_by TEXT,
                    recorded_at TEXT NOT NULL
                );
            """)
        self._init_fts()

    def _init_fts(self) -> None:
        """Initializes FTS5 virtual table knowledge_fts if available."""
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
        except sqlite3.OperationalError:
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

    def index_document(
        self, entry_id: str, title: str, content: str, tags: str = "", file_path: str = ""
    ) -> None:
        """Indexes a document into SQLite knowledge_fts table."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO knowledge_fts (entry_id, title, content, tags, file_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entry_id, title, content, tags, file_path),
            )

    def query_fts(self, query: str, limit: int = 5) -> list[RAGResult]:
        """Queries full-text search index."""
        if not query.strip():
            return []

        cursor = self._conn.cursor()
        results: list[RAGResult] = []

        if getattr(self, "_has_fts", False):
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
                    raw_path = row["file_path"] or "docs/memory.md"
                    score = abs(float(row["rank"])) if row["rank"] is not None else 1.0
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
            for row in rows:
                raw_path = row["file_path"] or "docs/memory.md"
                snippet = str(row["content"])[:200]
                results.append(
                    RAGResult(
                        file_path=ArtifactPath(raw_path),
                        score=0.75,
                        snippet=snippet,
                        matched_lines=[1],
                    )
                )
        except Exception as exc:
            logger.warning(f"LIKE fallback query failed: {exc}")

        return results

    def query_vector(self, query_text: str, limit: int = 5) -> list[dict[str, Any]]:
        """Queries Qdrant REST endpoint with 1.0s timeout."""
        endpoint = f"{self.qdrant_url}/collections/ai-skill-framework/points/search"
        payload = json.dumps({"vector": [0.0] * 128, "limit": limit}).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    body = json.loads(response.read().decode("utf-8"))
                    return body.get("result", [])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            logger.warning(f"Qdrant connection failed or timed out: {exc}")

        return []

    def save_state(self, state: WorkflowState) -> None:
        """Saves WorkflowState entity to database."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO workflow_states (session_id, active_phase, checkpoint, status, started_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    active_phase=excluded.active_phase,
                    checkpoint=excluded.checkpoint,
                    status=excluded.status,
                    started_at=excluded.started_at,
                    updated_at=excluded.updated_at;
                """,
                (
                    state.session_id,
                    state.active_phase,
                    state.checkpoint,
                    state.status.value,
                    state.started_at.isoformat(),
                    state.updated_at.isoformat(),
                ),
            )

    def get_state(self, session_id: str) -> WorkflowState:
        """Retrieves WorkflowState entity for session_id.

        Raises:
            EntityNotFoundError: If session record does not exist.
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT session_id, active_phase, checkpoint, status, started_at, updated_at FROM workflow_states WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise EntityNotFoundError(f"Session '{session_id}' not found in SQLite store.")

        return WorkflowState(
            session_id=row["session_id"],
            active_phase=row["active_phase"],
            checkpoint=int(row["checkpoint"]),
            status=PhaseStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def record_checkpoint(self, checkpoint: Checkpoint, session_id: str = "default") -> None:
        """Records a Checkpoint entity."""
        val_by = checkpoint.validated_by.value if checkpoint.validated_by else None
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO checkpoints (session_id, sequence, phase, status, validated_by, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    checkpoint.sequence,
                    checkpoint.phase,
                    checkpoint.status.value,
                    val_by,
                    checkpoint.recorded_at.isoformat(),
                ),
            )

    def list_checkpoints(self, session_id: str) -> list[Checkpoint]:
        """Lists all Checkpoints for session_id."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT sequence, phase, status, validated_by, recorded_at FROM checkpoints WHERE session_id = ? ORDER BY sequence ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        return [
            Checkpoint(
                sequence=row["sequence"],
                phase=row["phase"],
                status=PhaseStatus(row["status"]),
                validated_by=RoleId(row["validated_by"]) if row["validated_by"] else None,
                recorded_at=datetime.fromisoformat(row["recorded_at"]),
            )
            for row in rows
        ]

    def close(self) -> None:
        """Closes database connection."""
        self._conn.close()
