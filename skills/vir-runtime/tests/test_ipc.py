# File path: tests/unit/test_ipc.py
import unittest
import io
import json
from vir_runtime.core.ipc import IPCEmitter

class TestIPCEmitter(unittest.TestCase):
    def test_emit_event(self):
        stream = io.StringIO()
        emitter = IPCEmitter(stream=stream)
        
        payload = {"stage": "Reason", "duration": 1.2}
        emitter.emit_event("stage_done", payload)
        
        # Verify output is valid NDJSON
        stream.seek(0)
        output_line = stream.readline().strip()
        
        parsed = json.loads(output_line)
        self.assertEqual(parsed["type"], "stage_done")
        self.assertEqual(parsed["payload"]["stage"], "Reason")

if __name__ == "__main__":
    unittest.main()
