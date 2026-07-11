import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from virtual_process_manager import VirtualProcessManager

def test_virtual_process_spawn_and_kill():
    manager = VirtualProcessManager()
    
    # Run a simple python echo process
    vpid = manager.spawn([sys.executable, "-c", "import time; time.sleep(10)"])
    assert vpid in manager.process_table
    assert manager.process_table[vpid]["status"] == "RUNNING"
    
    # Kill the process
    success = manager.send_signal(vpid, "SIGKILL")
    assert success is True
    
    # Verify exit status
    proc_info = manager.reap(vpid)
    assert proc_info["status"] == "TERMINATED"
