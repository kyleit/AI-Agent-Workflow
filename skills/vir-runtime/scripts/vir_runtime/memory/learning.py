# File path: vir_runtime/memory/learning.py
import sqlite3
import json
import time
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class LearningOutcome:
    session_id: str
    feature_id: str
    verdict: str
    lessons_learned: List[str]

class LearningEngine:
    def __init__(self, db_path: str = "vir_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_learnings (
                    session_id TEXT PRIMARY KEY,
                    feature_id TEXT,
                    outcome_data TEXT,
                    vector_embeddings TEXT,
                    timestamp REAL
                );
            """)
        conn.close()

    def process_investigation_close(self, session_details: Dict[str, Any]) -> None:
        """Extract session LearningOutcome structures and serialize lessons."""
        session_id = session_details.get("session_id", "unknown_session")
        feature_id = session_details.get("feature_id", "FEAT-000")
        verdict = session_details.get("verdict", "PASS")
        
        # Build lessons learned based on issues/resolutions
        lessons = []
        if verdict == "FAIL":
            reasons = session_details.get("fail_reasons", [])
            for r in reasons:
                lessons.append(f"Avoid failure: {r}")
        else:
            lessons.append(f"Successfully verified {feature_id} flow path layouts.")

        outcome = LearningOutcome(
            session_id=session_id,
            feature_id=feature_id,
            verdict=verdict,
            lessons_learned=lessons
        )

        # Mock vector embeddings mapping
        mock_embedding = [0.1] * 128 # 128-dim mock vector

        # Save to SQLite vir_learnings
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO vir_learnings (session_id, feature_id, outcome_data, vector_embeddings, timestamp)
                VALUES (?, ?, ?, ?, ?);
            """, (
                session_id, 
                feature_id, 
                json.dumps(outcome.__dict__), 
                json.dumps(mock_embedding), 
                time.time()
            ))
        conn.close()
        print(f"[LearningEngine] Saved learning outcome for session {session_id}")

    def query_lessons(self, feature_id: str) -> List[Dict[str, Any]]:
        """Query historical lessons outcomes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT outcome_data FROM vir_learnings WHERE feature_id = ?;", (feature_id,))
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
