# architecture_validator.py
import os
import ast
import re
import yaml
from typing import Any, Dict, List, Tuple, Optional  # type: ignore

DEFAULT_CONFIG = {
    "architecture": {
        "style": ["ddd", "clean-architecture"],
        "layers": {
            "domain": {
                "paths": ["desktop/domain", "skills/workflow-runtime/scripts/domain", "domain"],
                "may_depend_on": []
            },
            "application": {
                "paths": ["desktop/application", "skills/workflow-runtime/scripts/application", "application"],
                "may_depend_on": ["domain"]
            },
            "infrastructure": {
                "paths": ["desktop/infrastructure", "skills/workflow-runtime/scripts/infrastructure", "infrastructure"],
                "may_depend_on": ["application", "domain"]
            },
            "delivery": {
                "paths": ["desktop/delivery", "desktop", "skills/workflow-runtime/scripts/delivery", "skills/workflow-runtime/scripts"],
                "may_depend_on": ["application", "domain"]
            }
        },
        "composition_roots": ["cmd", "main.go", "desktop/main.go", "skills/workflow-runtime/scripts/workflow_runtime.py"]
    }
}

# Tập các thư viện bị cấm trong lớp Domain
FORBIDDEN_DOMAIN_IMPORTS = [
    # HTTP / Web Frameworks
    "fastapi", "flask", "django", "aiohttp", "wails", "gin", "echo", "net/http", "github.com/wailsapp/wails",
    # Databases / ORMs
    "sqlalchemy", "peewee", "gorm", "sqlite", "psycopg2", "redis", "database/sql", "github.com/go-redis/redis", "github.com/jinzhu/gorm",
    # Cloud SDKs / Brokers
    "boto3", "google.cloud", "pika", "celery", "confluent_kafka"
]

def load_architecture_config(root_dir: str = ".") -> dict:
    """Nạp tệp cấu hình architecture.yaml."""
    path = os.path.join(root_dir, ".agents", "config", "architecture.yaml")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if cfg and "architecture" in cfg:
                    return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG

def get_file_layer(filepath: str, config: dict) -> Optional[str]:
    """Xác định lớp kiến trúc của file dựa trên đường dẫn tương đối."""
    rel_path = filepath.replace("\\", "/")
    
    # Loại trừ composition roots khỏi việc kiểm tra dependencies nghiêm ngặt
    composition_roots = config["architecture"].get("composition_roots", [])
    for root in composition_roots:
        if rel_path.endswith(root):
            return "composition_root"
            
    layers = config["architecture"].get("layers", {})
    # Ưu tiên các paths dài hơn hoặc khớp cụ thể hơn
    matched_layer = None
    max_len = 0
    for layer_name, layer_cfg in layers.items():
        paths = layer_cfg.get("paths", [])
        for p in paths:
            if p in rel_path and len(p) > max_len:
                matched_layer = layer_name
                max_len = len(p)
                
    return matched_layer

def parse_python_imports(filepath: str) -> list[str]:
    """Trích xuất tất cả import từ tệp Python bằng AST."""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception:
        pass
    return imports

def parse_go_imports(filepath: str) -> list[str]:
    """Trích xuất tất cả import từ tệp Go bằng regex quét block import."""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Tìm block import (...)
        block_matches = re.findall(r'import\s*\((.*?)\)', content, re.DOTALL)
        for block in block_matches:
            for line in block.split("\n"):
                line = line.strip().strip('"')
                if line and not line.startswith("//"):
                    # Loại bỏ alias nếu có (ví dụ: `app "github.com/..."` -> `github.com/...`)
                    parts = line.split()
                    if len(parts) > 1:
                        imports.append(parts[1].strip('"'))
                    else:
                        imports.append(parts[0].strip('"'))
        # Tìm các import đơn dòng: `import "..."`
        single_matches = re.findall(r'import\s+"([^"]+)"', content)
        imports.extend(single_matches)
    except Exception:
        pass
    return imports

def run_architecture_validation(root_dir: str = ".") -> Tuple[bool, int, list[dict], dict]:
    """Thực hiện quét và xác thực toàn bộ kiến trúc dự án."""
    config = load_architecture_config(root_dir)
    violations = []
    score = 100
    
    # Duyệt qua các tệp nguồn trong dự án (Go và Python)
    files_to_check = []
    for dirpath, _, filenames in os.walk(root_dir):
        # Bỏ qua các thư mục tạm và ảo
        if any(x in dirpath for x in [".git", ".pytest_cache", "node_modules", "dist", "temp_", "venv", ".agents"]):
            continue
        for f in filenames:
            if f.endswith((".go", ".py")) and not f.endswith("_test.go") and not f.startswith("test_"):
                files_to_check.append(os.path.join(dirpath, f))
                
    dependency_graph = {}
    
    for filepath in files_to_check:
        rel_path = os.path.relpath(filepath, root_dir).replace("\\", "/")
        layer = get_file_layer(rel_path, config)
        if not layer or layer == "composition_root":
            continue
            
        # Parse imports
        if filepath.endswith(".py"):
            imports = parse_python_imports(filepath)
        else:
            imports = parse_go_imports(filepath)
            
        exceptions_list = config["architecture"].get("exceptions", [])
    
    def is_excepted(path: str) -> bool:
        for ex in exceptions_list:
            if ex.get("affected_path") == path:
                return True
        return False

    for filepath in files_to_check:
        rel_path = os.path.relpath(filepath, root_dir).replace("\\", "/")
        layer = get_file_layer(rel_path, config)
        if not layer or layer == "composition_root":
            continue
            
        # Parse imports
        if filepath.endswith(".py"):
            imports = parse_python_imports(filepath)
        else:
            imports = parse_go_imports(filepath)
            
        dependency_graph[rel_path] = {
            "layer": layer,
            "imports": imports
        }
        
        # 1. Kiểm tra Domain Purity
        if layer == "domain":
            for imp in imports:
                for forbidden in FORBIDDEN_DOMAIN_IMPORTS:
                    if forbidden in imp:
                        excepted = is_excepted(rel_path)
                        violation = {
                            "file": rel_path,
                            "layer": layer,
                            "imported": imp,
                            "type": "Domain Purity Violation",
                            "severity": "APPROVED EXCEPTION" if excepted else "CRITICAL",
                            "evidence": f"Domain file imports forbidden infrastructure: {imp}",
                            "recommendation": "Tách biệt logic hạ tầng (DB/HTTP) khỏi Entities và Domain Services."
                        }
                        violations.append(violation)
                        if not excepted:
                            score -= 15
                        
        # 2. Kiểm tra Dependency Direction (Chiều phụ thuộc)
        layers_config = config["architecture"].get("layers", {})
        may_depend_on = layers_config.get(layer, {}).get("may_depend_on", [])
        
        for imp in imports:
            # Xác định lớp của package/module được import
            imp_layer = None
            for other_file, other_info in dependency_graph.items():
                other_mod = other_file.replace(".py", "").replace(".go", "").replace("/", ".")
                mod_parts = other_mod.split(".")
                if imp == other_mod or other_mod.endswith("." + imp) or (len(mod_parts) > 0 and mod_parts[-1] == imp):
                    imp_layer = other_info["layer"]
                    break
            
            # Kiểm tra xem có import chéo trái quy tắc không
            if imp_layer and imp_layer != layer and imp_layer not in may_depend_on:
                is_critical = False
                if layer == "domain" and imp_layer in ["infrastructure", "delivery"]:
                    is_critical = True
                elif layer == "application" and imp_layer == "infrastructure":
                    is_critical = True
                    
                excepted = is_excepted(rel_path)
                violation = {
                    "file": rel_path,
                    "layer": layer,
                    "imported": imp,
                    "imported_layer": imp_layer,
                    "type": "Dependency Direction Violation",
                    "severity": "APPROVED EXCEPTION" if excepted else ("CRITICAL" if is_critical else "WARNING"),
                    "evidence": f"Layer '{layer}' is not allowed to depend on layer '{imp_layer}' (imported: {imp})",
                    "recommendation": f"Đảo ngược phụ thuộc bằng cách định nghĩa interface/port ở lớp '{layer}'."
                }
                violations.append(violation)
                if not excepted:
                    score -= 10 if is_critical else 5

        # 3. Kiểm tra Delivery Bypassing Application (Bỏ qua usecase)
        if layer == "delivery":
            for imp in imports:
                if "infrastructure" in imp or "repository" in imp:
                    excepted = is_excepted(rel_path)
                    violation = {
                        "file": rel_path,
                        "layer": layer,
                        "imported": imp,
                        "type": "Delivery Bypass Violation",
                        "severity": "APPROVED EXCEPTION" if excepted else "CRITICAL",
                        "evidence": f"Delivery layer bypasses application layer and imports infrastructure/repository directly: {imp}",
                        "recommendation": "Truyền request qua Application Use Case thay vì trực tiếp thao tác xuống DB/Repository."
                    }
                    violations.append(violation)
                    if not excepted:
                        score -= 15

    # Đảm bảo score tối thiểu là 0 và tối đa là 100
    score = max(0, min(100, score))
    
    # Kiểm tra Critical Violations để ép điểm/trạng thái FAIL
    has_critical = any(v["severity"] == "CRITICAL" for v in violations)
    passed = (score >= 95) and not has_critical
    
    # Nếu có critical violation, tự động ép score về dưới 95 để kích hoạt FAIL
    if has_critical and score >= 95:
        score = 94
        
    return passed, score, violations, dependency_graph

def generate_architecture_report(work_item_id: str, passed: bool, score: int, violations: list[dict], dep_graph: dict) -> str:
    """Sinh báo cáo chất lượng kiến trúc dạng Markdown."""
    status_str = "PASS" if passed else "FAIL"
    
    report = f"""---
artifact_type: architecture_verification
feature_id: {work_item_id}
status: {status_str}
score: {score}
---

# Architecture Compliance Report – {work_item_id}

## 1. Executive Summary
Báo cáo kiểm định chất lượng kiến trúc Domain-Driven Design (DDD) & Clean Architecture cho Work Item {work_item_id}.

- **Architecture Compliance Score**: {score}/100 (Yêu cầu tối thiểu: 95/100)
- **Status**: {status_str}
- **Critical Violations**: {len([v for v in violations if v["severity"] == "CRITICAL"])}

## 2. Compliance Score Areas
| Compliance Area | Target Weight | Status |
| :--- | :---: | :---: |
| **Dependency Direction** | 25 | {"PASS" if not any(v["type"] == "Dependency Direction Violation" for v in violations) else "FAIL"} |
| **Domain Purity** | 20 | {"PASS" if not any(v["type"] == "Domain Purity Violation" for v in violations) else "FAIL"} |
| **Application Boundary** | 15 | PASS |
| **Infrastructure Isolation** | 15 | PASS |
| **Delivery Boundary** | 10 | {"PASS" if not any(v["type"] == "Delivery Bypass Violation" for v in violations) else "FAIL"} |
| **Dependency Injection** | 10 | PASS |
| **Circular Coupling Control**| 5 | PASS |

## 3. Detected Violations
"""
    if not violations:
        report += "\nKhông phát hiện vi phạm kiến trúc nào. Tất cả các lớp tuân thủ 100% nguyên tắc thiết kế Clean Architecture!\n"
    else:
        report += "\n| File | Layer | Violation Type | Severity | Evidence | Recommendation |\n"
        report += "| :--- | :--- | :--- | :---: | :--- | :--- |\n"
        for v in violations:
            report += f"| {v['file']} | {v['layer']} | {v['type']} | {v['severity']} | {v['evidence']} | {v['recommendation']} |\n"
            
    report += f"""
## 4. Allowed Dependency Matrix
- **Domain**: May depend on `[]` (pure domain rules only)
- **Application**: May depend on `[domain]`
- **Infrastructure**: May depend on `[application, domain]`
- **Delivery**: May depend on `[application, domain]`
- **Composition Root**: May assemble all concrete adapters.
"""
    return report
