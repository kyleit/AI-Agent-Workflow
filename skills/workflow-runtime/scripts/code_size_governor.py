# code_size_governor.py
import os
import ast
import re
import json
try:
    import yaml
except ImportError:
    yaml = None
from typing import Any, Dict, List, Tuple, Optional

DEFAULT_POLICY = {
    "enabled": True,
    "max_lines_per_file": 500,
    "warning_lines_per_file": 400,
    "max_lines_per_function": 60,
    "warning_lines_per_function": 45,
    "max_methods_per_class": 20,
    "max_class_lines": 300,
    "allow_generated_code": True,
    "exclude": [
        "dist/**",
        "build/**",
        ".venv/**",
        "node_modules/**"
    ],
    "exceptions": []
}

def load_code_size_policy(root_dir: str = ".") -> Dict:
    """Nạp cấu hình code_size_policy từ architecture.yaml."""
    path = os.path.join(root_dir, ".agents", "config", "architecture.yaml")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if cfg and "architecture" in cfg and "code_size_policy" in cfg["architecture"]:
                    return cfg["architecture"]["code_size_policy"]
                elif cfg and "code_size_policy" in cfg:
                    return cfg["code_size_policy"]
        except Exception:
            pass
    return DEFAULT_POLICY

def is_excluded(filepath: str, exclude_patterns: List[str]) -> bool:
    """Kiểm tra xem file có thuộc danh sách loại trừ không."""
    normalized_path = filepath.replace("\\", "/")
    for pattern in exclude_patterns:
        # Chuyển đổi wildcard pattern đơn giản sang regex
        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*")
        if re.search(regex_pattern, normalized_path):
            return True
    return False

def analyze_python_file(filepath: str, policy: Dict) -> Dict:
    """Phân tích AST kích thước code cho tệp Python."""
    metrics = {
        "file_lines": 0,
        "classes": [],
        "functions": []
    }
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
            
        metrics["file_lines"] = len(code.splitlines())
        tree = ast.parse(code, filename=filepath)
        
        for node in ast.walk(tree):
            # 1. Đo kích thước hàm tự do (không nằm trong class)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Kiểm tra xem hàm có phải là method của class hay không
                # Bằng cách xem node cha của nó trong AST walk (ta có thể kiểm tra thủ công)
                # Để đơn giản, ta tính tất cả các hàm/methods
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line)
                lines = end_line - start_line + 1
                
                metrics["functions"].append({
                    "name": node.name,
                    "lines": lines,
                    "start_line": start_line,
                    "end_line": end_line
                })
                
            # 2. Đo kích thước class và methods
            elif isinstance(node, ast.ClassDef):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line)
                class_lines = end_line - start_line + 1
                
                methods = []
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sub_start = subnode.lineno
                        sub_end = getattr(subnode, "end_lineno", sub_start)
                        methods.append({
                            "name": subnode.name,
                            "lines": sub_end - sub_start + 1
                        })
                        
                metrics["classes"].append({
                    "name": node.name,
                    "lines": class_lines,
                    "methods_count": len(methods),
                    "methods": methods
                })
    except Exception:
        pass
        
    return metrics

def analyze_go_file(filepath: str, policy: Dict) -> Dict:
    """Phân tích kích thước code cho tệp Go."""
    metrics = {
        "file_lines": 0,
        "classes": [], # Go structs
        "functions": []
    }
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        metrics["file_lines"] = len(lines)
        
        # Phân tích hàm Go bằng thuật toán đếm ngoặc nhọn cân bằng
        in_func = False
        func_name = ""
        func_start = 0
        bracket_count = 0
        
        for idx, line in enumerate(lines):
            line_str = line.strip()
            
            # Phát hiện định nghĩa hàm Go
            if not in_func:
                match = re.match(r"^func\s+(?:\([^)]+\)\s+)?([A-Za-z0-9_]+)\(", line_str)
                if match:
                    func_name = match.group(1)
                    func_start = idx + 1
                    in_func = True
                    bracket_count = 0
                    
            if in_func:
                bracket_count += line_str.count("{")
                bracket_count -= line_str.count("}")
                if bracket_count <= 0 and idx + 1 > func_start:
                    func_lines = idx + 1 - func_start + 1
                    metrics["functions"].append({
                        "name": func_name,
                        "lines": func_lines,
                        "start_line": func_start,
                        "end_line": idx + 1
                    })
                    in_func = False
                    
        # Phân tích struct Go (tương đương classes)
        in_struct = False
        struct_name = ""
        struct_start = 0
        struct_bracket = 0
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not in_struct:
                match = re.match(r"^type\s+([A-Za-z0-9_]+)\s+struct", line_str)
                if match:
                    struct_name = match.group(1)
                    struct_start = idx + 1
                    in_struct = True
                    struct_bracket = 0
            if in_struct:
                struct_bracket += line_str.count("{")
                struct_bracket -= line_str.count("}")
                if struct_bracket <= 0 and idx + 1 > struct_start:
                    struct_lines = idx + 1 - struct_start + 1
                    # Đếm số methods thuộc struct này (Go receiver methods)
                    methods_count = 0
                    for f in metrics["functions"]:
                        # Phân tích receiver
                        # Ví dụ: func (a *App) Action() -> receiver is App
                        pass
                    metrics["classes"].append({
                        "name": struct_name,
                        "lines": struct_bracket,
                        "methods_count": methods_count,
                        "methods": []
                    })
                    in_struct = False
    except Exception:
        pass
        
    return metrics

def run_code_size_audit(root_dir: str = ".") -> Tuple[bool, List[Dict], Dict]:
    """Chạy phân tích toàn diện kích thước code."""
    policy = load_code_size_policy(root_dir)
    if not policy.get("enabled", True):
        return True, [], {}
        
    violations = []
    all_metrics = {
        "largest_files": [],
        "largest_functions": [],
        "largest_classes": [],
        "violations_count": 0
    }
    
    files_to_check = []
    exclude_patterns = policy.get("exclude", [])
    
    for dirpath, _, filenames in os.walk(root_dir):
        if any(x in dirpath for x in [".git", "node_modules", "dist", ".pytest_cache", ".agents", "venv"]):
            continue
        for f in filenames:
            if f.endswith((".go", ".py")):
                filepath = os.path.join(dirpath, f)
                rel_path = os.path.relpath(filepath, root_dir).replace("\\", "/")
                if not is_excluded(rel_path, exclude_patterns):
                    files_to_check.append((filepath, rel_path))
                    
    # helper check exceptions
    exceptions_list = policy.get("exceptions", [])
    def is_excepted(path: str) -> bool:
        for ex in exceptions_list:
            aff = ex.get("affected_path", "")
            if aff and (path == aff or path.endswith(aff) or aff in path):
                return True
        return False

    for filepath, rel_path in files_to_check:
        if filepath.endswith(".py"):
            metrics = analyze_python_file(filepath, policy)
        else:
            metrics = analyze_go_file(filepath, policy)
            
        file_lines = metrics["file_lines"]
        all_metrics["largest_files"].append({"file": rel_path, "lines": file_lines})
        
        # 1. Kiểm tra giới hạn File lines
        max_file_lines = policy.get("max_lines_per_file", 500)
        warn_file_lines = policy.get("warning_lines_per_file", 400)
        
        excepted = is_excepted(rel_path)
        
        if file_lines > max_file_lines:
            # Gợi ý refactor tách nhỏ file thành các lớp/hàm con
            rec = f"Split file into smaller module files (e.g. {os.path.basename(rel_path).replace('.py','')}Core, {os.path.basename(rel_path).replace('.py','')}Helper)."
            violations.append({
                "file": rel_path,
                "scope": "File",
                "name": rel_path,
                "current_lines": file_lines,
                "limit": max_file_lines,
                "status": "APPROVED EXCEPTION" if excepted else "FAIL",
                "recommendation": rec
            })
        elif file_lines > warn_file_lines:
            violations.append({
                "file": rel_path,
                "scope": "File",
                "name": rel_path,
                "current_lines": file_lines,
                "limit": warn_file_lines,
                "status": "WARNING",
                "recommendation": "Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ."
            })
            
        # 2. Kiểm tra giới hạn Functions
        max_func_lines = policy.get("max_lines_per_function", 60)
        warn_func_lines = policy.get("warning_lines_per_function", 45)
        
        for func in metrics["functions"]:
            all_metrics["largest_functions"].append({
                "file": rel_path,
                "name": func["name"],
                "lines": func["lines"]
            })
            
            if func["lines"] > max_func_lines:
                violations.append({
                    "file": rel_path,
                    "scope": "Function",
                    "name": func["name"],
                    "current_lines": func["lines"],
                    "limit": max_func_lines,
                    "status": "APPROVED EXCEPTION" if excepted else "FAIL",
                    "recommendation": f"Trích xuất mã nguồn trong hàm '{func['name']}' thành các hàm con (helper functions)."
                })
            elif func["lines"] > warn_func_lines:
                violations.append({
                    "file": rel_path,
                    "scope": "Function",
                    "name": func["name"],
                    "current_lines": func["lines"],
                    "limit": warn_func_lines,
                    "status": "WARNING",
                    "recommendation": f"Xem xét chia tách logic phức tạp trong hàm '{func['name']}'."
                })
                
        # 3. Kiểm tra giới hạn Classes
        max_class_lines = policy.get("max_class_lines", 300)
        max_methods = policy.get("max_methods_per_class", 20)
        
        for cls in metrics["classes"]:
            all_metrics["largest_classes"].append({
                "file": rel_path,
                "name": cls["name"],
                "lines": cls["lines"],
                "methods_count": cls["methods_count"]
            })
            
            if cls["lines"] > max_class_lines:
                violations.append({
                    "file": rel_path,
                    "scope": "Class",
                    "name": cls["name"],
                    "current_lines": cls["lines"],
                    "limit": max_class_lines,
                    "status": "APPROVED EXCEPTION" if excepted else "FAIL",
                    "recommendation": f"Tách lớp '{cls['name']}' thành các lớp con chuyên trách (SRP)."
                })
            if cls["methods_count"] > max_methods:
                violations.append({
                    "file": rel_path,
                    "scope": "ClassMethods",
                    "name": cls["name"],
                    "current_lines": cls["methods_count"],
                    "limit": max_methods,
                    "status": "APPROVED EXCEPTION" if excepted else "FAIL",
                    "recommendation": f"Lớp '{cls['name']}' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper."
                })

    # Sắp xếp top metrics
    all_metrics["largest_files"] = sorted(all_metrics["largest_files"], key=lambda x: x["lines"], reverse=True)[:10]
    all_metrics["largest_functions"] = sorted(all_metrics["largest_functions"], key=lambda x: x["lines"], reverse=True)[:10]
    all_metrics["largest_classes"] = sorted(all_metrics["largest_classes"], key=lambda x: x["lines"], reverse=True)[:10]
    
    # Tính số lượng vi phạm thực tế (không tính APPROVED EXCEPTION)
    real_failures = [v for v in violations if v["status"] == "FAIL"]
    all_metrics["violations_count"] = len(violations)
    
    passed = len(real_failures) == 0
    return passed, violations, all_metrics

def generate_code_size_report(work_item_id: str, passed: bool, violations: List[Dict], metrics: Dict) -> str:
    """Sinh báo cáo Markdown Code Size Governance."""
    status_str = "PASS" if passed else "FAIL"
    
    report = f"""---
artifact_type: code_size_verification
feature_id: {work_item_id}
status: {status_str}
violations_count: {metrics.get("violations_count", 0)}
---

# Code Size Governance Report – {work_item_id}

## 1. Executive Summary
Báo cáo kiểm soát kích thước mã nguồn và nợ kỹ thuật cho Work Item {work_item_id}.

- **File Size Policy**: {"PASS" if not any(v["scope"] == "File" and v["status"] == "FAIL" for v in violations) else "FAIL"}
- **Function Size Policy**: {"PASS" if not any(v["scope"] == "Function" and v["status"] == "FAIL" for v in violations) else "FAIL"}
- **Class Size Policy**: {"PASS" if not any(v["scope"] in ["Class", "ClassMethods"] and v["status"] == "FAIL" for v in violations) else "FAIL"}
- **Overall Status**: {status_str}

## 2. Policy Violations & Recommendations
"""
    if not violations:
        report += "\nKhông phát hiện vi phạm kích thước mã nguồn nào. Tất cả các tệp tin, lớp và hàm đều nằm dưới ngưỡng giới hạn!\n"
    else:
        report += "\n| File | Scope | Name | Current Size / Lines | Policy Limit | Status | Recommendation |\n"
        report += "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n"
        for v in violations:
            report += f"| {v['file']} | {v['scope']} | {v['name']} | {v['current_lines']} | {v['limit']} | {v['status']} | {v['recommendation']} |\n"
            
    report += "\n## 3. Code Metric Dashboards\n"
    report += "### Largest Files\n"
    report += "| File | Lines |\n| :--- | :---: |\n"
    for f in metrics.get("largest_files", []):
        report += f"| {f['file']} | {f['lines']} |\n"
        
    report += "\n### Largest Functions\n"
    report += "| File | Function Name | Lines |\n| :--- | :--- | :---: |\n"
    for func in metrics.get("largest_functions", []):
        report += f"| {func['file']} | {func['name']} | {func['lines']} |\n"
        
    report += "\n### Largest Classes\n"
    report += "| File | Class Name | Lines | Methods |\n| :--- | :--- | :---: | :---: |\n"
    for cls in metrics.get("largest_classes", []):
        report += f"| {cls['file']} | {cls['name']} | {cls['lines']} | {cls['methods_count']} |\n"
        
    return report
