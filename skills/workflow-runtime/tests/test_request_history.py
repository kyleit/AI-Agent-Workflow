# test_request_history.py
import unittest
import os
import sys
import sqlite3
import shutil
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
import db
from context import sync_request_history

class TestRequestHistory(unittest.TestCase):
    def setUp(self):
        # Override project DB for testing
        self.test_dir = os.path.join(os.path.dirname(__file__), "temp_test_db")
        os.makedirs(self.test_dir, exist_ok=True)
        self.original_db = db.PROJECT_DB
        db.PROJECT_DB = os.path.join(self.test_dir, "test_runtime.db")
        
        # Setup mock session file
        self.session_file = os.path.join(".agents", ".session.json")
        self.original_session_content = None
        if os.path.exists(self.session_file):
            with open(self.session_file, "r", encoding="utf-8") as f:
                self.original_session_content = f.read()
                
        # Write clean session for tests
        session_data = {
            "conversation_id": "test_conversation_999",
            "current_skill": "workflow-runtime",
            "current_command": "step"
        }
        os.makedirs(".agents", exist_ok=True)
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

    def tearDown(self):
        # Restore db path
        db.PROJECT_DB = self.original_db
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        # Restore session file
        if self.original_session_content is not None:
            try:
                with open(self.session_file, "w", encoding="utf-8") as f:
                    f.write(self.original_session_content)
            except Exception:
                pass
        elif os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
            except Exception:
                pass

    def test_database_migration(self):
        # Trigger schema initialization via saving a request
        req = {
            "request_id": "req_1",
            "workflow_id": "wf_1",
            "conversation_id": "conv_1",
            "project_id": "proj_1",
            "skill_name": "test-skill",
            "command_name": "test-cmd",
            "model": "gemini-2.5",
            "provider": "antigravity",
            "timestamp": "2026-07-09T00:00:00Z",
            "duration": 5.2,
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_tokens": 15,
            "thinking_tokens": 5,
            "total_tokens": 150,
            "cost_usd": 0.00035,
            "tool_call_count": 2,
            "workspace_read_count": 5,
            "memory_hit_count": 1,
            "rag_hit_count": 3,
            "context_usage_percentage": 10.5,
            "context_limit_tokens": 2000000,
            "context_breakdown_json": "{}",
            "status": "success",
            "error_summary": None
        }
        
        db.save_provider_request(req)
        
        # Verify db file is created and tables/indexes are present
        self.assertTrue(os.path.exists(db.PROJECT_DB))
        conn = sqlite3.connect(db.PROJECT_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provider_requests'")
        self.assertIsNotNone(cursor.fetchone())
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_requests_project_id'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()

    def test_prevent_duplicates(self):
        req = {
            "request_id": "unique_req_123",
            "workflow_id": "wf_1",
            "conversation_id": "conv_1",
            "project_id": "proj_1",
            "skill_name": "test-skill",
            "command_name": "test-cmd",
            "model": "gemini-2.5",
            "provider": "antigravity",
            "timestamp": "2026-07-09T00:00:00Z",
            "duration": 5.2,
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_tokens": 15,
            "thinking_tokens": 5,
            "total_tokens": 150,
            "cost_usd": 0.00035,
            "tool_call_count": 2,
            "workspace_read_count": 5,
            "memory_hit_count": 1,
            "rag_hit_count": 3,
            "context_usage_percentage": 10.5,
            "context_limit_tokens": 2000000,
            "context_breakdown_json": "{}",
            "status": "success",
            "error_summary": None
        }
        
        # Save twice
        db.save_provider_request(req)
        db.save_provider_request(req)
        
        conn = sqlite3.connect(db.PROJECT_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM provider_requests WHERE request_id = 'unique_req_123'")
        count = cursor.fetchone()[0]
        conn.close()
        
        # Should be exactly 1 due to INSERT OR IGNORE
        self.assertEqual(count, 1)

    def test_sorting_by_cost(self):
        req1 = {
            "request_id": "req_1", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_1", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.01, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000
        }
        req2 = {
            "request_id": "req_2", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_1", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.05, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000
        }
        
        db.save_provider_request(req1)
        db.save_provider_request(req2)
        
        # Fetch requests sorted by cost desc
        results = db.get_provider_requests({}, sort_by="cost_usd", desc=True)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["request_id"], "req_2") # Highest cost first
        self.assertEqual(results[1]["request_id"], "req_1")

    def test_filtering_by_skill(self):
        req1 = {
            "request_id": "req_1", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_target", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.01, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000
        }
        req2 = {
            "request_id": "req_2", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_other", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.05, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000
        }
        
        db.save_provider_request(req1)
        db.save_provider_request(req2)
        
        results = db.get_provider_requests({"skill_name": "skill_target"})
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["request_id"], "req_1")

    def test_filtering_by_time_range(self):
        req1 = {
            "request_id": "req_1", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_1", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.01, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000,
            "timestamp": "2026-07-09T01:00:00Z"
        }
        req2 = {
            "request_id": "req_2", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_1", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.05, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000,
            "timestamp": "2026-07-09T03:00:00Z"
        }
        req3 = {
            "request_id": "req_3", "workflow_id": "wf_1", "conversation_id": "conv_1", "project_id": "proj_1",
            "skill_name": "skill_1", "command_name": "cmd_1", "model": "m", "provider": "p", "status": "success",
            "cost_usd": 0.05, "duration": 1.0, "input_tokens": 10, "output_tokens": 10, "cache_tokens": 0, "thinking_tokens": 0, "total_tokens": 20,
            "tool_call_count": 0, "workspace_read_count": 0, "memory_hit_count": 0, "rag_hit_count": 0, "context_usage_percentage": 0.0, "context_limit_tokens": 2000000,
            "timestamp": "2026-07-09T05:00:00Z"
        }
        
        db.save_provider_request(req1)
        db.save_provider_request(req2)
        db.save_provider_request(req3)
        
        # Test start_time only
        res = db.get_provider_requests({"start_time": "2026-07-09T02:00:00Z"}, sort_by="timestamp", desc=False)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["request_id"], "req_2")
        self.assertEqual(res[1]["request_id"], "req_3")
        
        # Test end_time only
        res = db.get_provider_requests({"end_time": "2026-07-09T04:00:00Z"}, sort_by="timestamp", desc=False)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["request_id"], "req_1")
        self.assertEqual(res[1]["request_id"], "req_2")
        
        # Test both
        res = db.get_provider_requests({"start_time": "2026-07-09T02:00:00Z", "end_time": "2026-07-09T04:00:00Z"})
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["request_id"], "req_2")

if __name__ == "__main__":
    unittest.main()
