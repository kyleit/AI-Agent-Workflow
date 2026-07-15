import pytest
from safe_multi_agent_writes import ParallelWriteValidator

def test_parallel_writes_disjoint():
    validator = ParallelWriteValidator(".")
    packages = [
        {"write_set": ["src/module_a/file1.py", "src/module_a/file2.py"]},
        {"write_set": ["src/module_b/file1.py", "src/module_b/file3.py"]}
    ]
    # Disjoint write sets should be allowed
    assert validator.validate_parallel_execution(packages) is True

def test_parallel_writes_overlap():
    validator = ParallelWriteValidator(".")
    packages = [
        {"write_set": ["src/module_a/file1.py", "src/module_b/file1.py"]},
        {"write_set": ["src/module_b/file1.py", "src/module_b/file3.py"]}
    ]
    # Overlapping write sets should be blocked (return False)
    assert validator.validate_parallel_execution(packages) is False

def test_global_file_conflicts():
    validator = ParallelWriteValidator(".")
    
    # Conflict when modifying requirements.txt
    packages_conflict = [
        {"write_set": ["src/module_a/file1.py", "requirements.txt"]}
    ]
    assert validator.check_global_file_conflicts(packages_conflict) is True
    
    # No conflict for normal module files
    packages_safe = [
        {"write_set": ["src/module_a/file1.py", "src/module_a/file2.py"]}
    ]
    assert validator.check_global_file_conflicts(packages_safe) is False
