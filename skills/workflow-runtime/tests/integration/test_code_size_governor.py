# test_code_size_governor.py
import os
import json
import pytest
import yaml
from code_size_governor import (
    load_code_size_policy,
    is_excluded,
    analyze_python_file,
    analyze_go_file,
    run_code_size_audit
)

def test_load_code_size_policy(tmp_path):
    # Test fallback to DEFAULT_POLICY if file not found
    policy = load_code_size_policy(str(tmp_path))
    assert policy["enabled"] is True
    assert policy["max_lines_per_file"] == 500

    # Test loading actual config
    config_dir = tmp_path / ".agents" / "config"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "architecture.yaml"
    
    custom_policy = {
        "code_size_policy": {
            "enabled": True,
            "max_lines_per_file": 200,
            "warning_lines_per_file": 150,
            "max_lines_per_function": 40,
            "warning_lines_per_function": 30,
            "max_methods_per_class": 10,
            "max_class_lines": 150,
            "allow_generated_code": True,
            "exclude": ["test_exclude/**"],
            "exceptions": []
        }
    }
    
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(custom_policy, f)
        
    policy = load_code_size_policy(str(tmp_path))
    assert policy["max_lines_per_file"] == 200

def test_is_excluded():
    exclude_patterns = ["dist/**", "build/**", "node_modules/**", "test_exclude/*.py"]
    
    assert is_excluded("dist/bundle.js", exclude_patterns) is True
    assert is_excluded("src/app.py", exclude_patterns) is False
    assert is_excluded("test_exclude/dummy.py", exclude_patterns) is True

def test_analyze_python_file(tmp_path):
    py_file = tmp_path / "test_file.py"
    content = """# Test File
def func_a(x):
    # line 1
    # line 2
    return x * 2

class App:
    def method_1(self):
        pass
        
    def method_2(self):
        print("Hello")
"""
    py_file.write_text(content, encoding="utf-8")
    
    policy = {
        "max_lines_per_file": 500,
        "max_lines_per_function": 60
    }
    metrics = analyze_python_file(str(py_file), policy)
    
    assert metrics["file_lines"] == 12
    assert len(metrics["functions"]) == 3
    assert len(metrics["classes"]) == 1
    assert metrics["classes"][0]["name"] == "App"
    assert metrics["classes"][0]["methods_count"] == 2

def test_analyze_go_file(tmp_path):
    go_file = tmp_path / "test_file.go"
    content = """package main

import "fmt"

func Hello(name string) {
    fmt.Printf("Hello %s", name)
}

type Config struct {
    Port int
}
"""
    go_file.write_text(content, encoding="utf-8")
    
    policy = {
        "max_lines_per_file": 500,
        "max_lines_per_function": 60
    }
    metrics = analyze_go_file(str(go_file), policy)
    
    assert metrics["file_lines"] == 11
    assert len(metrics["functions"]) == 1
    assert metrics["functions"][0]["name"] == "Hello"
    assert len(metrics["classes"]) == 1
    assert metrics["classes"][0]["name"] == "Config"

def test_run_code_size_audit(tmp_path):
    # Setup test workspace
    config_dir = tmp_path / ".agents" / "config"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "architecture.yaml"
    
    custom_policy = {
        "code_size_policy": {
            "enabled": True,
            "max_lines_per_file": 10,
            "warning_lines_per_file": 8,
            "max_lines_per_function": 4,
            "warning_lines_per_function": 3,
            "max_methods_per_class": 10,
            "max_class_lines": 150,
            "allow_generated_code": True,
            "exclude": ["test_exclude/**"],
            "exceptions": [
                {
                    "affected_path": "excepted.py",
                    "reason": "Legacy code wrapper",
                    "owner": "Ba",
                    "expiration_date": "2026-12-31"
                }
            ]
        }
    }
    
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(custom_policy, f)
        
    # Write oversized file that is not excepted
    oversized = tmp_path / "oversized.py"
    oversized.write_text("\n" * 15, encoding="utf-8") # 16 lines > 10
    
    # Write oversized file that is excepted
    excepted = tmp_path / "excepted.py"
    excepted.write_text("\n" * 15, encoding="utf-8")
    
    passed, violations, all_metrics = run_code_size_audit(str(tmp_path))
    
    # Should fail due to oversized.py
    assert passed is False
    
    # Verify exceptions mapping
    oversized_violation = next(v for v in violations if v["file"] == "oversized.py")
    excepted_violation = next(v for v in violations if v["file"] == "excepted.py")
    
    assert oversized_violation["status"] == "FAIL"
    assert excepted_violation["status"] == "APPROVED EXCEPTION"
