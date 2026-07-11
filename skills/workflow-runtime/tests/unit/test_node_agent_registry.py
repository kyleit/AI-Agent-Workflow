import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from node_agent_registry import NodeAgentRegistry
import sqlite3

def test_node_agent_registry_lifecycle(tmp_path):
    db_file = tmp_path / "nodes.db"
    registry = NodeAgentRegistry(db_path=str(db_file))
    
    # Normal registration
    assert registry.register_worker("worker_1", 4) is True
    
    # Path traversal block check
    assert registry.register_worker("worker_1/../../malicious", 2) is False
    
    # Verification
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT worker_id, capacity, status FROM active_nodes;")
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0] == ("worker_1", 4, "ACTIVE")
    conn.close()
