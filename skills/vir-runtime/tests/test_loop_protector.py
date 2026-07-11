# File path: tests/unit/test_loop_protector.py
import unittest
from vir_runtime.core.loop_protector import LoopProtector
from vir_runtime.core.bus import Event

class TestLoopProtector(unittest.TestCase):
    def test_loop_detection(self):
        protector = LoopProtector(max_history=10, repeat_threshold=2)
        
        event1 = Event("vir.evidence.new", {"type": "contradiction"})
        event2 = Event("vir.evidence.new", {"type": "contradiction"})
        event3 = Event("vir.evidence.new", {"type": "contradiction"})

        # First occurrences should be fine
        self.assertFalse(protector.inspect_event(event1))
        self.assertFalse(protector.inspect_event(event2))
        
        # Third occurrence should be flagged as loop
        self.assertTrue(protector.inspect_event(event3))

    def test_different_payloads(self):
        protector = LoopProtector(max_history=10, repeat_threshold=2)
        
        event1 = Event("vir.evidence.new", {"value": 1})
        event2 = Event("vir.evidence.new", {"value": 2})
        event3 = Event("vir.evidence.new", {"value": 1})

        self.assertFalse(protector.inspect_event(event1))
        self.assertFalse(protector.inspect_event(event2))
        self.assertFalse(protector.inspect_event(event3))

if __name__ == "__main__":
    unittest.main()
