# fingerprint_engine.py
# SHA-256 fingerprint engine with SQLite deduplication checking
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from typing import Dict, Optional

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
    pass


class FingerprintEngine:
    """
    Computes deterministic SHA-256 fingerprints from raw provider payload fields
    and registers them in the `request_fingerprints` table to prevent double-counting.
    """

    def __init__(self, db_conn: sqlite3.Connection):
        """
        Args:
            db_conn: Active SQLite connection to check and register fingerprints.
        """
        self._conn = db_conn

    def compute(self, fields: dict) -> str:
        """
        Compute a 64-character lowercase hex SHA-256 fingerprint based on canonical fields.

        Args:
            fields: Dictionary containing keys: provider, conversation_id, request_id,
                    response_id, model, timestamp, and raw_payload or payload_hash.

        Returns:
            64-character lowercase hex string. Never raises (falls back to empty values on miss).
        """
        try:
            # Determine payload hash
            payload_hash = fields.get("payload_hash", "")
            if not payload_hash and "raw_payload" in fields and fields["raw_payload"]:
                payload_hash = self._compute_payload_hash(fields["raw_payload"])

            canonical_data = {}
            for field in CANONICAL_FIELDS:
                if field == "payload_hash":
                    canonical_data[field] = payload_hash or ""
                else:
                    canonical_data[field] = str(fields.get(field, "") or "")

            # Serialize deterministically
            canonical_json = json.dumps(
                canonical_data,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True
            )
            return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        except Exception as e:
            # Fallback to a hash based on timestamp/process info if hashing fails (defensive)
            fallback_str = f"fallback-{datetime.now().isoformat()}-{id(fields)}"
            return hashlib.sha256(fallback_str.encode("utf-8")).hexdigest()

    def is_duplicate(self, fingerprint: str) -> bool:
        """
        Check if the fingerprint already exists in the request_fingerprints database.

        Args:
            fingerprint: 64-character fingerprint string.

        Returns:
            True if duplicate exists, False otherwise.
        """
        if not fingerprint:
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

    def register(self, fingerprint: str, metadata: dict) -> bool:
        """
        Register a new fingerprint. If a duplicate exists, increment duplicate_count.

        Args:
            fingerprint: 64-character fingerprint string.
            metadata: Dict with provider, conv_id, request_id, model, timestamp.

        Returns:
            True if new fingerprint registered, False if collision/duplicate.
        """
        if not fingerprint:
            return False
        try:
            cursor = self._conn.cursor()
            now_iso = datetime.now().astimezone().isoformat()

            # Deduplication checking
            cursor.execute(
                "SELECT duplicate_count FROM request_fingerprints WHERE fingerprint = ? LIMIT 1",
                (fingerprint,)
            )
            row = cursor.fetchone()

            if row is not None:
                # Collision: update counters and last seen
                dup_count = row[0] + 1
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

            # Brand new fingerprint
            provider = metadata.get("provider", "") or ""
            conv_id = metadata.get("conversation_id", "") or metadata.get("conv_id", "") or ""
            request_id = metadata.get("request_id", "") or ""
            model = metadata.get("model", "") or ""
            timestamp = metadata.get("timestamp", "") or now_iso

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

    def get_stats(self) -> dict:
        """
        Return global registration and duplicate counters.
        """
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

    def _compute_payload_hash(self, raw_payload: dict) -> str:
        """Helper to hash the raw payload dict deterministically."""
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
