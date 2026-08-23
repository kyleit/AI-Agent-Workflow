import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from execution_queue_checkpoint import ExecutionQueueCheckpointManager
import sqlite3

def test_queue_scheduling_and_checkpoints(tmp_path):
    db_file = tmp_path / "execution_queue.db"
    manager = ExecutionQueueCheckpointManager(db_path=str(db_file))
    
    # Enqueue items with different priorities
    manager.enqueue({
        "queue_id": "q1",
        "objective_id": "obj1",
        "program_id": "prog1",
        "sprint_id": "sprint1",
        "feat_id": "FEAT-109",
        "priority": 10
    })
    manager.enqueue({
        "queue_id": "q2",
        "objective_id": "obj1",
        "program_id": "prog1",
        "sprint_id": "sprint1",
        "feat_id": "FEAT-110",
        "priority": 20
    })
    
    # Dequeue should yield the highest priority first (q2 has priority 20)
    item = manager.dequeue()
    assert item is not None
    assert item["queue_id"] == "q2"
    
    # Checkpoint saving & loading
    manager.save_checkpoint("chk_1", {"status": "SUCCESS", "last_task": "Task 1.1"})
    chk = manager.load_checkpoint("chk_1")
    assert chk is not None
    assert chk["status"] == "SUCCESS"
    assert chk["last_task"] == "Task 1.1"
