import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from virtual_filesystem_overlay import VirtualFilesystemOverlay

def test_vfs_read_write(tmp_path):
    vfs = VirtualFilesystemOverlay()
    virtual_file = str(tmp_path / "virtual.py")
    
    vfs.write_virtual(virtual_file, "print('hello')")
    assert vfs.read_virtual(virtual_file) == "print('hello')"
    
    # File should not exist on disk yet
    assert not os.path.exists(virtual_file)
    
    # Commit changes
    vfs.commit_vfs()
    assert os.path.exists(virtual_file)
    with open(virtual_file, "r") as f:
        assert f.read() == "print('hello')"
    
    os.remove(virtual_file)
