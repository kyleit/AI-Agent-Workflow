# test_event_store.py
import pytest
import os
import sys

# Add script directory to sys.path to find event_store
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from event_store import SQLiteEventStore, JournalCorruptedError

def test_event_store_append_and_retrieve(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session_id = "test-session-id"
    
    store.append_event(session_id=session_id, topic="test.event", payload={"data": "hello"})
    store.append_event(session_id=session_id, topic="test.event.2", payload={"number": 42})
    
    events = store.get_events(session_id=session_id)
    assert len(events) == 2
    assert events[0]["topic"] == "test.event"
    assert events[0]["payload"]["data"] == "hello"
    assert events[1]["topic"] == "test.event.2"
    assert events[1]["payload"]["number"] == 42

def test_event_store_clear(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session_id = "test-session-id"
    
    store.append_event(session_id=session_id, topic="test.event", payload={"data": "hello"})
    store.clear_session_events(session_id=session_id)
    
    events = store.get_events(session_id=session_id)
    assert len(events) == 0
