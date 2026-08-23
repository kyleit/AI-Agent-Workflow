import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from interactive_terminal_process_monitor import InteractiveTerminalMonitor

def test_interactive_terminal_monitor():
    monitor = InteractiveTerminalMonitor()
    output = monitor.run_interactive([sys.executable, "-c", "print('hello from subprocess')"])
    assert "hello from subprocess" in output
    assert "hello from subprocess" in monitor.log_buffer
