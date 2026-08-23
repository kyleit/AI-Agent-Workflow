# test_post_release_lifecycle.py
import pytest
import os
import sys

# Add script directory to sys.path to find post_release_lifecycle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from post_release_lifecycle import PostReleaseLifecycleAutomator

def test_post_release_lifecycle_automation(tmp_path):
    out_dir = str(tmp_path / "reviews")
    automator = PostReleaseLifecycleAutomator(
        release_version="6.14.2",
        git_commit="1f7f0e7",
        output_dir=out_dir
    )
    
    reports = automator.run_all_phases()
    
    # Verify all files are created and recorded
    assert os.path.exists(reports["post_release_validation"])
    assert os.path.exists(reports["runtime_roadmap"])
    
    # Verify content format inside a generated report
    with open(reports["post_release_validation"], "r", encoding="utf-8") as f:
        content = f.read()
        assert "6.14.2" in content
        assert "1f7f0e7" in content
        assert "SUCCESS" in content
