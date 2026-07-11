# File path: tests/unit/test_reporting_engine.py
import unittest
import os
import tempfile
import json
from vir_runtime.reporting.engine import ReportPublisher
from vir_runtime.reporting.packager import ZipPackager

class TestReporting(unittest.IsolatedAsyncioTestCase):
    async def test_publish_and_pack(self):
        # Create temp dirs
        tmp_output_dir = tempfile.TemporaryDirectory()
        tmp_json_dir = tempfile.TemporaryDirectory()
        
        publisher = ReportPublisher(output_dir=tmp_output_dir.name, json_dir=tmp_json_dir.name)
        
        session_details = {
            "feature_id": "FEAT-999",
            "verdict": "PASS",
            "peak_ram_mb": 12.4,
            "timeline_events": [
                {"stage": "Observe", "status": "PASS", "timestamp": 123},
                {"stage": "Understand", "status": "PASS", "timestamp": 124}
            ]
        }
        
        md_path, json_path = await publisher.publish_report(session_details, "FEAT-999")
        
        self.assertTrue(os.path.exists(md_path))
        self.assertTrue(os.path.exists(json_path))

        # Test ZIP packaging
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            zip_path = tmp_zip.name
            
        try:
            ZipPackager.create_session_zip("session_123", [md_path, json_path], zip_path)
            self.assertTrue(os.path.exists(zip_path))
            self.assertGreater(os.path.getsize(zip_path), 0)
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            tmp_output_dir.cleanup()
            tmp_json_dir.cleanup()

if __name__ == "__main__":
    unittest.main()
