# File path: tests/unit/test_learning.py
import unittest
import tempfile
import os
from vir_runtime.memory.learning import LearningEngine

class TestLearningEngine(unittest.TestCase):
    def setUp(self):
        # Create temp DB path
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            self.db_path = tmp.name
        self.engine = LearningEngine(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_process_close_and_query(self):
        session_details = {
            "session_id": "sess_abc",
            "feature_id": "FEAT-111",
            "verdict": "FAIL",
            "fail_reasons": ["UI mismatch on hero image", "Performance lag on type"]
        }
        
        self.engine.process_investigation_close(session_details)
        lessons = self.engine.query_lessons("FEAT-111")
        
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["verdict"], "FAIL")
        self.assertEqual(len(lessons[0]["lessons_learned"]), 2)
        self.assertIn("hero image", lessons[0]["lessons_learned"][0])

if __name__ == "__main__":
    unittest.main()
