# File path: vir_runtime/domain/evidence_engine.py
from __future__ import annotations

import json
import sqlite3
from typing import Any

from workflow_runtime.domain.visual.core.evidence import Evidence


class EvidenceEngine:
    def __init__(self, db_path: str = "vir_state.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    source_agent TEXT,
                    classification TEXT,
                    payload TEXT,
                    timestamp REAL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_investigations (
                    investigation_id TEXT PRIMARY KEY,
                    status TEXT,
                    feature_id TEXT
                );
            """)
        conn.close()

    def add_evidence(self, evidence: Evidence) -> None:
        """Store new evidence records inside the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        payload_str = json.dumps(evidence.payload)
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO vir_evidence (evidence_id, source_agent, classification, payload, timestamp)
                VALUES (?, ?, ?, ?, ?);
            """, (evidence.evidence_id, evidence.source_agent, evidence.classification, payload_str, evidence.timestamp))
        conn.close()

    def query_evidence(self, filter_criteria: dict[str, Any]) -> list[Evidence]:
        """Query stored evidence filters in database matching key value constraints."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT evidence_id, source_agent, classification, payload, timestamp FROM vir_evidence"
        conditions: list[str] = []
        params: list[Any] = []
        for key, value in filter_criteria.items():
            conditions.append(f"{key} = ?")
            params.append(value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        evidence_list: list[Evidence] = []
        for row in rows:
            evidence_list.append(
                Evidence(
                    evidence_id=str(row[0]),
                    source_agent=str(row[1]),
                    classification=str(row[2]),
                    payload=json.loads(str(row[3])),
                    timestamp=float(row[4])
                )
            )
        return evidence_list


__all__ = ["EvidenceEngine"]
