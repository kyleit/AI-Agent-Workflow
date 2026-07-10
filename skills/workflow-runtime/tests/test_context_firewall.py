# test_context_firewall.py
import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from context_firewall import ContextFirewall, ProjectContextViolationError

class TestContextFirewall(unittest.TestCase):
    def setUp(self):
        self.scope = {
            "project_id": "test-project",
            "workspace_root": os.path.abspath(os.path.dirname(__file__)),
            "git_root": os.path.abspath(os.path.dirname(__file__)),
            "allow_cross_project_context": False
        }
        self.firewall = ContextFirewall(self.scope)

    def test_validate_context_path_inside_scope(self):
        # Current file path should be valid
        self.assertTrue(self.firewall.validate_context_path(__file__))

    def test_validate_context_path_outside_scope(self):
        # Accessing /etc/passwd or similar outside scope should raise error
        with self.assertRaises(ProjectContextViolationError):
            self.firewall.validate_context_path("/etc/passwd")

    def test_validate_context_path_special_allowance(self):
        # App Data Directory paths should be allowed
        app_data_path = "/Users/username/.gemini/antigravity-ide/brain/123/transcript.jsonl"
        self.assertTrue(self.firewall.validate_context_path(app_data_path))

    def test_validate_conversation_valid(self):
        history = [
            {"metadata": {"project_id": "test-project"}},
            {"metadata": {"project_id": "test-project"}}
        ]
        self.assertTrue(self.firewall.validate_conversation(history, "test-project"))

    def test_validate_conversation_invalid(self):
        history = [
            {"metadata": {"project_id": "test-project"}},
            {"metadata": {"project_id": "other-project"}}
        ]
        self.assertFalse(self.firewall.validate_conversation(history, "test-project"))

    def test_filter_rag_results(self):
        results = [
            {"metadata": {"project_id": "test-project"}, "text": "doc1"},
            {"metadata": {"project_id": "other-project"}, "text": "doc2"},
            {"text": "doc3"} # no project_id should pass by default
        ]
        filtered = self.firewall.filter_rag_results(results)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["text"], "doc1")
        self.assertEqual(filtered[1]["text"], "doc3")

if __name__ == "__main__":
    unittest.main()
