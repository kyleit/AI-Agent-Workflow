# test_architecture_validator.py
import os
import unittest
import shutil
import tempfile
import yaml
import sys
import os

# Thêm thư mục scripts vào sys.path để tránh lỗi import dấu gạch ngang
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from architecture_validator import (
    parse_python_imports,
    parse_go_imports,
    run_architecture_validation,
    generate_architecture_report
)

class TestArchitectureValidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Tạo cấu hình architecture.yaml giả lập
        self.config = {
            "architecture": {
                "style": ["ddd", "clean-architecture"],
                "layers": {
                    "domain": {
                        "paths": ["domain"],
                        "may_depend_on": []
                    },
                    "application": {
                        "paths": ["application"],
                        "may_depend_on": ["domain"]
                    },
                    "infrastructure": {
                        "paths": ["infrastructure"],
                        "may_depend_on": ["application", "domain"]
                    },
                    "delivery": {
                        "paths": ["delivery"],
                        "may_depend_on": ["application", "domain"]
                    }
                },
                "composition_roots": ["main.py", "main.go"],
                "exceptions": [
                    {
                        "affected_path": "domain/legacy.py",
                        "reason": "Legacy test exception",
                        "owner": "Test",
                        "expiration_date": "2026-12-31",
                        "related_adr": "ADR-001"
                    }
                ]
            }
        }
        
        # Ghi file cấu hình
        config_dir = os.path.join(self.test_dir, ".agents", "config")
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "architecture.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(self.config, f)
            
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_parse_python_imports(self):
        py_file = os.path.join(self.test_dir, "test_imports.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("import os\nfrom typing import Dict, List\nimport fastapi\n")
            
        imports = parse_python_imports(py_file)
        self.assertIn("os", imports)
        self.assertIn("typing", imports)
        self.assertIn("fastapi", imports)
        
    def test_parse_go_imports(self):
        go_file = os.path.join(self.test_dir, "test_imports.go")
        with open(go_file, "w", encoding="utf-8") as f:
            f.write('package main\nimport "fmt"\nimport (\n\t"os"\n\tnet "net/http"\n)\n')
            
        imports = parse_go_imports(go_file)
        self.assertIn("fmt", imports)
        self.assertIn("os", imports)
        self.assertIn("net/http", imports)
        
    def test_architecture_validation_pass(self):
        # Tạo cấu trúc file sạch tuân thủ Clean Architecture
        domain_dir = os.path.join(self.test_dir, "domain")
        app_dir = os.path.join(self.test_dir, "application")
        
        os.makedirs(domain_dir, exist_ok=True)
        os.makedirs(app_dir, exist_ok=True)
        
        # Domain không import bậy bạ
        with open(os.path.join(domain_dir, "model.py"), "w", encoding="utf-8") as f:
            f.write("class User: pass\n")
            
        # Application service import domain
        with open(os.path.join(app_dir, "service.py"), "w", encoding="utf-8") as f:
            f.write("from domain.model import User\n")
            
        passed, score, violations, _ = run_architecture_validation(self.test_dir)
        self.assertTrue(passed)
        self.assertEqual(score, 100)
        self.assertEqual(len(violations), 0)
        
    def test_architecture_validation_fail_purity(self):
        domain_dir = os.path.join(self.test_dir, "domain")
        os.makedirs(domain_dir, exist_ok=True)
        
        # Domain vi phạm purity (import fastapi và sqlalchemy)
        with open(os.path.join(domain_dir, "model.py"), "w", encoding="utf-8") as f:
            f.write("import fastapi\nimport sqlalchemy\n")
            
        passed, score, violations, _ = run_architecture_validation(self.test_dir)
        self.assertFalse(passed)
        self.assertLess(score, 95)
        self.assertTrue(any(v["type"] == "Domain Purity Violation" for v in violations))
        
    def test_architecture_validation_exceptions(self):
        domain_dir = os.path.join(self.test_dir, "domain")
        os.makedirs(domain_dir, exist_ok=True)
        
        # Domain vi phạm purity nhưng nằm trong config exceptions (domain/legacy.py)
        with open(os.path.join(domain_dir, "legacy.py"), "w", encoding="utf-8") as f:
            f.write("import sqlite3\n")
            
        passed, score, violations, _ = run_architecture_validation(self.test_dir)
        # Điểm đạt 100 vì vi phạm được miễn trừ qua exceptions
        self.assertTrue(passed)
        self.assertEqual(score, 100)
        self.assertTrue(any(v["severity"] == "APPROVED EXCEPTION" for v in violations))
        
    def test_generate_report(self):
        report = generate_architecture_report("FEAT-115", True, 100, [], {})
        self.assertIn("Architecture Compliance Report", report)
        self.assertIn("100/100", report)
        self.assertIn("PASS", report)
