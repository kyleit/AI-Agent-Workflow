# test_update_source.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from update_source import SourceRepositoryService

class TestUpdateSource(unittest.TestCase):
    @patch("update_source.SourceRepositoryService._run_git")
    @patch("os.path.exists")
    def test_check_status_clean(self, mock_exists, mock_run_git):
        mock_exists.return_value = True
        
        # Mock Git commands outputs:
        # symbolic-ref -q HEAD -> refs/heads/main
        # branch --show-current -> main
        # rev-parse --abbrev-ref @{u} -> origin/main
        # rev-parse HEAD -> commit_abc
        # diff-index --quiet HEAD -- -> 0 (clean)
        # status --porcelain -> "" (no untracked)
        # fetch -> 0
        # rev-parse origin/main -> commit_abc (up-to-date)
        def run_git_mock(args):
            if "symbolic-ref" in args:
                return 0, "refs/heads/main", ""
            elif "branch" in args:
                return 0, "main", ""
            elif "rev-parse" in args and "@{u}" in args:
                return 0, "origin/main", ""
            elif "rev-parse" in args and "origin/main" in args:
                return 0, "commit_abc", ""
            elif "rev-parse" in args and "HEAD" in args:
                return 0, "commit_abc", ""
            elif "diff-index" in args:
                return 0, "", ""
            elif "status" in args:
                return 0, "", ""
            elif "fetch" in args:
                return 0, "", ""
            return 0, "", ""
            
        mock_run_git.side_effect = run_git_mock
        
        service = SourceRepositoryService(source_path="/fake/repo", remote="origin", branch="main")
        status = service.check_status()
        
        self.assertEqual(status["status"], "success")
        self.assertTrue(status["is_up_to_date"])
        self.assertFalse(status["is_dirty"])

    @patch("update_source.SourceRepositoryService._run_git")
    @patch("os.path.exists")
    def test_check_status_dirty(self, mock_exists, mock_run_git):
        mock_exists.return_value = True
        
        def run_git_mock(args):
            if "symbolic-ref" in args:
                return 0, "refs/heads/main", ""
            elif "branch" in args:
                return 0, "main", ""
            elif "rev-parse" in args and "@{u}" in args:
                return 0, "origin/main", ""
            elif "rev-parse" in args and "origin/main" in args:
                return 0, "commit_xyz", ""
            elif "rev-parse" in args and "HEAD" in args:
                return 0, "commit_abc", ""
            elif "diff-index" in args:
                return 1, "dirty changes", "" # dirty
            elif "status" in args:
                return 0, "?? untracked.txt", ""
            elif "fetch" in args:
                return 0, "", ""
            return 0, "", ""
            
        mock_run_git.side_effect = run_git_mock
        
        service = SourceRepositoryService(source_path="/fake/repo", remote="origin", branch="main")
        status = service.check_status()
        
        self.assertEqual(status["status"], "success")
        self.assertTrue(status["is_dirty"])

if __name__ == "__main__":
    unittest.main()
