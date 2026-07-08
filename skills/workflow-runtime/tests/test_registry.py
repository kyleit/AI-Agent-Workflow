import os
import sys
import json
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust sys.path to resolve scripts imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import aiwf_registry

@pytest.fixture
def temp_registry_dir(tmp_path):
    """Fixture to mock registry folder and reset global paths."""
    registry_path = tmp_path / "projects.json"
    
    with patch("aiwf_registry.get_registry_path", return_value=registry_path), \
         patch("aiwf_registry.get_registry_dir", return_value=tmp_path):
        yield tmp_path

def test_get_registry_path_creation(temp_registry_dir):
    """Test that the registry directory and path are created properly."""
    path = aiwf_registry.get_registry_path()
    assert path.name == "projects.json"
    assert path.parent == temp_registry_dir

def test_atomic_write(temp_registry_dir):
    """Test atomic write creates the registry JSON correctly."""
    data = {
        "schema_version": 1,
        "updated_at": "now",
        "projects": [{"id": "1", "name": "project1", "path": "/path/1", "status": "active"}]
    }
    aiwf_registry.save_registry_atomic(data)
    
    path = aiwf_registry.get_registry_path()
    assert path.exists()
    
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["schema_version"] == 1
    assert loaded["projects"][0]["name"] == "project1"

def test_corrupted_json_recovery(temp_registry_dir):
    """Test registry recovery and auto-backup when projects.json contains invalid JSON."""
    path = aiwf_registry.get_registry_path()
    
    # Write invalid JSON content
    with open(path, "w", encoding="utf-8") as f:
        f.write("invalid json string {hello: world}")
        
    registry = aiwf_registry.load_registry()
    assert registry["schema_version"] == 1
    assert len(registry["projects"]) == 0
    
    # Verify backup exists
    backups = list(temp_registry_dir.glob("projects.json.bak.*"))
    assert len(backups) == 1
    
    # Verify backup contains the corrupted content
    with open(backups[0], "r", encoding="utf-8") as f:
        content = f.read()
    assert "invalid json string" in content

def test_idempotent_register(temp_registry_dir, tmp_path):
    """Test that registering same project twice is idempotent."""
    project_dir = tmp_path / "my-project"
    project_dir.mkdir()
    (project_dir / ".agents").mkdir()
    (project_dir / ".agents" / "AI_RULES.md").write_text("# Rules")
    (project_dir / ".agents" / "skills").mkdir()
    
    # First registration
    res = aiwf_registry.register_project(str(project_dir))
    assert res["status"] == "success"
    
    registry = aiwf_registry.load_registry()
    assert len(registry["projects"]) == 1
    
    # Second registration (idempotent)
    res2 = aiwf_registry.register_project(str(project_dir))
    assert res2["status"] == "success"
    
    registry2 = aiwf_registry.load_registry()
    assert len(registry2["projects"]) == 1

def test_path_normalization_windows():
    """Test Windows case-insensitive normalization logic."""
    with patch("platform.system", return_value="Windows"):
        p1 = aiwf_registry.normalize_path("C:\\MyProject")
        p2 = aiwf_registry.normalize_path("c:\\myproject")
        assert str(p1) == str(p2)

def test_cleanup_registry(temp_registry_dir, tmp_path):
    """Test registry cleanup removes non-existent folders."""
    p1 = tmp_path / "exists"
    p1.mkdir()
    (p1 / ".agents").mkdir()
    (p1 / ".agents" / "AI_RULES.md").write_text("# Rules")
    (p1 / ".agents" / "skills").mkdir()
    
    p2 = tmp_path / "missing"
    p2.mkdir()
    
    # Register p1 and p2 (using force for missing .agents)
    aiwf_registry.register_project(str(p1))
    aiwf_registry.register_project(str(p2), force=True)
    
    # Now remove p2 directory to make it "missing"
    p2.rmdir()
    
    registry = aiwf_registry.load_registry()
    assert len(registry["projects"]) == 2
    
    # Cleanup
    cleanup_res = aiwf_registry.cleanup_registry()
    assert cleanup_res["total_removed"] == 1
    assert cleanup_res["removed_paths"][0] == str(aiwf_registry.normalize_path(p2))
    
    registry2 = aiwf_registry.load_registry()
    assert len(registry2["projects"]) == 1
    assert registry2["projects"][0]["name"] == "exists"

@patch("subprocess.run")
def test_update_all_projects(mock_run, temp_registry_dir, tmp_path):
    """Test batch updating active registered projects."""
    p1 = tmp_path / "proj1"
    p1.mkdir()
    (p1 / ".agents").mkdir()
    (p1 / ".agents" / "AI_RULES.md").write_text("# Rules")
    (p1 / ".agents" / "skills").mkdir()
    
    aiwf_registry.register_project(str(p1))
    
    # Mock subprocess completion success
    mock_run.return_value = MagicMock(returncode=0)
    
    summary = aiwf_registry.update_all_projects()
    assert summary["total"] == 1
    assert summary["updated"] == 1
    assert summary["failed"] == 0
    assert summary["missing"] == 0
    
    assert mock_run.call_count == 1
