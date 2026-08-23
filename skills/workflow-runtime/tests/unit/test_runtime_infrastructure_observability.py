import sys
import os
import json
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from runtime_infrastructure_observability import EventJournal

def test_event_journal_logging(tmp_path):
    db_file = tmp_path / "journal.db"
    ndjson_file = tmp_path / "event_stream.ndjson"
    
    journal = EventJournal(db_path=str(db_file), fallback_path=str(ndjson_file))
    journal.log_event("TEST_START", {"message": "hello"})
    
    # Wait for async thread to flush queue
    time.sleep(0.5)
    journal.stop()
    
    # Verify NDJSON log file fallback
    assert os.path.exists(str(ndjson_file))
    with open(str(ndjson_file), "r", encoding="utf-8") as f:
        line = f.readline().strip()
        data = json.loads(line)
        assert data["event_type"] == "TEST_START"
        assert data["payload"]["message"] == "hello"
        
    # Verify SQLite file was populated
    import sqlite3
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT event_type, payload FROM journal;")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "TEST_START"
    assert json.loads(row[1])["message"] == "hello"
    conn.close()
