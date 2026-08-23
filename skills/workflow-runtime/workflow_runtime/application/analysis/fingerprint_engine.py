# fingerprint_engine.py
# SHA-256 fingerprint engine with SQLite deduplication checking
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Any, cast

CANONICAL_FIELDS = [
    "provider",
    "conversation_id",
    "request_id",
    "response_id",
    "model",
    "timestamp",
    "payload_hash"
]


class FingerprintEngineError(RuntimeError):
    """Custom exception raised by FingerprintEngine on database or parsing failures."""


class FingerprintEngine:
    """
    Computes deterministic SHA-256 fingerprints from raw provider payload fields
    and registers them in the `request_fingerprints` table to prevent double-counting.
    """

    def __init__(self, db_conn: sqlite3.Connection | None = None) -> None:
        self._conn = db_conn

    def compute(self, fields: dict[str, Any]) -> str:
        """
        Compute a 64-character lowercase hex SHA-256 fingerprint based on canonical fields.
        """
        try:
            payload_hash = str(fields.get("payload_hash", "") or "")
            raw_pl = fields.get("raw_payload")
            if not payload_hash and raw_pl and isinstance(raw_pl, dict):
                payload_hash = self._compute_payload_hash(cast(dict[str, Any], raw_pl))

            canonical_data: dict[str, str] = {}
            for field in CANONICAL_FIELDS:
                if field == "payload_hash":
                    canonical_data[field] = payload_hash or ""
                else:
                    canonical_data[field] = str(fields.get(field, "") or "")

            canonical_json = json.dumps(
                canonical_data,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True
            )
            return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        except Exception:
            fallback_str = f"fallback-{datetime.now().isoformat()}-{id(fields)}"
            return hashlib.sha256(fallback_str.encode("utf-8")).hexdigest()

    def is_duplicate(self, fingerprint: str) -> bool:
        if not fingerprint or self._conn is None:
            return False
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT 1 FROM request_fingerprints WHERE fingerprint = ? LIMIT 1",
                (fingerprint,)
            )
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            raise FingerprintEngineError(f"Database lookup failed for fingerprint {fingerprint}: {e}")

    def register(self, fingerprint: str, metadata: dict[str, Any]) -> bool:
        if not fingerprint or self._conn is None:
            return False
        try:
            cursor = self._conn.cursor()
            now_iso = datetime.now().astimezone().isoformat()

            cursor.execute(
                "SELECT duplicate_count FROM request_fingerprints WHERE fingerprint = ? LIMIT 1",
                (fingerprint,)
            )
            row = cursor.fetchone()

            if row is not None:
                dup_count = int(cast(int, row[0])) + 1
                cursor.execute(
                    """
                    UPDATE request_fingerprints
                    SET duplicate_count = ?, last_seen = ?
                    WHERE fingerprint = ?
                    """,
                    (dup_count, now_iso, fingerprint)
                )
                self._conn.commit()
                return False

            provider = str(metadata.get("provider", "") or "")
            conv_id = str(metadata.get("conversation_id", "") or metadata.get("conv_id", "") or "")
            request_id = str(metadata.get("request_id", "") or "")
            model = str(metadata.get("model", "") or "")
            timestamp = str(metadata.get("timestamp", "") or now_iso)

            cursor.execute(
                """
                INSERT INTO request_fingerprints (
                    fingerprint, provider, conv_id, request_id, model, timestamp,
                    duplicate_count, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (fingerprint, provider, conv_id, request_id, model, timestamp, now_iso, now_iso)
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            raise FingerprintEngineError(f"Failed to register fingerprint {fingerprint}: {e}")

    def get_stats(self) -> dict[str, Any]:
        if self._conn is None:
            return {"total_registered": 0, "total_duplicates": 0}
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(duplicate_count) FROM request_fingerprints")
            row = cursor.fetchone()
            if row:
                return {
                    "total_registered": row[0] or 0,
                    "total_duplicates": row[1] or 0
                }
            return {"total_registered": 0, "total_duplicates": 0}
        except sqlite3.Error:
            return {"total_registered": 0, "total_duplicates": 0}

    def _compute_payload_hash(self, raw_payload: dict[str, Any]) -> str:
        try:
            payload_json = json.dumps(
                raw_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True
            )
            return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()[:16]
        except Exception:
            return ""


__all__ = [
    "CANONICAL_FIELDS",
    "FingerprintEngineError",
    "FingerprintEngine",
]
