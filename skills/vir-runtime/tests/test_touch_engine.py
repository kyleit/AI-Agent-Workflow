# File path: tests/unit/test_touch_engine.py
import unittest
import os
import tempfile
from vir_runtime.sensory.touch import TouchEngine

class TestTouchEngine(unittest.IsolatedAsyncioTestCase):
    async def test_execute_and_replay(self):
        engine = TouchEngine()
        
        # Execute click in mode A
        await engine.execute_action({"type": "click", "selector": "#login-btn"}, mode="A")
        # Execute click in mode B (delay check)
        await engine.execute_action({"type": "type", "selector": "#username", "value": "kyle"}, mode="B")

        self.assertEqual(len(engine.action_history), 2)

        # Export replay log
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            engine.export_replay_log(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
