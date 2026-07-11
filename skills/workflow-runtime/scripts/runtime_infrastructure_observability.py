# runtime_infrastructure_observability.py
import sqlite3
import json
import time
import os
from queue import Queue
from threading import Thread

class EventJournal:
    """
    FEAT-089: Event Journal & Observability
    Performs asynchronous logging to SQLite WAL mode and fallback log files.
    """
    def __init__(self, db_path: str = ".agents/runtime/journal.db", fallback_path: str = ".agents/runtime/event_stream.ndjson"):
        self.db_path = db_path
        self.fallback_path = fallback_path
        self.queue = Queue()
        self.running = True
        self._init_db()
        self.worker_thread = Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    payload TEXT,
                    timestamp REAL
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def log_event(self, event_type: str, payload: dict) -> None:
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time()
        }
        self.queue.put(event)
        
        # Immediate sync fallback to NDJSON file stream
        try:
            os.makedirs(os.path.dirname(self.fallback_path), exist_ok=True)
            with open(self.fallback_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except IOError:
            pass

    def _process_queue(self) -> None:
        while self.running or not self.queue.empty():
            try:
                event = self.queue.get(timeout=0.1)
            except Exception:
                continue
                
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    "INSERT INTO journal (event_type, payload, timestamp) VALUES (?, ?, ?);",
                    (event["event_type"], json.dumps(event["payload"], ensure_ascii=False), event["timestamp"])
                )
                conn.commit()
            except sqlite3.Error:
                pass
            finally:
                conn.close()
            self.queue.task_done()

    def stop(self) -> None:
        self.running = False
        self.worker_thread.join()
