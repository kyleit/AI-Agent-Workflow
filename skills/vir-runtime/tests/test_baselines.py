# File path: tests/unit/test_baselines.py
import unittest
import tempfile
import os
from io import BytesIO
from PIL import Image
from vir_runtime.memory.baselines import BaselineManager

class TestBaselineManager(unittest.TestCase):
    def setUp(self):
        # Create temp DB path
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            self.db_path = tmp.name
        self.manager = BaselineManager(db_path=self.db_path)

        # Build mock png bytes
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        out = BytesIO()
        img.save(out, format="PNG")
        self.mock_png = out.getvalue()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_promote_and_get(self):
        self.manager.promote_new_baseline("FEAT-123", "/dashboard", "1440x900", self.mock_png)
        retrieved = self.manager.get_active_baseline("FEAT-123", "/dashboard", "1440x900")
        self.assertEqual(retrieved, self.mock_png)

    def test_check_regression_match(self):
        status = self.manager.check_regression(self.mock_png, self.mock_png)
        self.assertEqual(status, "MATCH")

if __name__ == "__main__":
    unittest.main()
