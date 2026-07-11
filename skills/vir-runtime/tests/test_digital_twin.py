# File path: tests/unit/test_digital_twin.py
import unittest
import tempfile
import os
from vir_runtime.twin.persistence import DigitalTwinManager

class TestDigitalTwin(unittest.IsolatedAsyncioTestCase):
    async def test_update_and_get(self):
        # Create a temporary DB path
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = DigitalTwinManager(db_path=db_path)
            
            # Verify initial empty state
            value = await manager.get_dimension_value("ui")
            self.assertEqual(value, {})

            # Update state dimension
            payload = {"status": "success", "active_tab": "dashboard"}
            await manager.update_dimension("ui", payload)

            # Retrieve from cache/DB
            retrieved = await manager.get_dimension_value("ui")
            self.assertEqual(retrieved["status"], "success")
            self.assertEqual(retrieved["active_tab"], "dashboard")

            # Force instantiate new manager to bypass cache and read directly from DB
            new_manager = DigitalTwinManager(db_path=db_path)
            db_retrieved = await new_manager.get_dimension_value("ui")
            self.assertEqual(db_retrieved["status"], "success")
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

if __name__ == "__main__":
    unittest.main()
