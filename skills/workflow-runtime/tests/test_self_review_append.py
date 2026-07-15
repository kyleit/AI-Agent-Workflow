import os
import pytest
from artifact_writer import append_self_review

def test_self_review_append(isolated_workspace):
    # Create dummy markdown file
    md_path = os.path.join(isolated_workspace, "test_doc.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("---\ntitle: Test\n---\n# Main Header\nSome content.")
        
    res = append_self_review(md_path, "Looks good to me.")
    
    assert res["status"] == "success"
    
    # Read file and verify content
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "## Agent Self-Review Comments" in content
    assert "Looks good to me." in content
    assert content.startswith("---") # yaml frontmatter preserved

def test_self_review_append_nonexistent_file(isolated_workspace):
    with pytest.raises(FileNotFoundError):
        append_self_review("nonexistent.md", "Comments")
