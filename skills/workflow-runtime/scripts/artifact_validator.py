# artifact_validator.py
import os
import yaml

REQUIRED_BLUEPRINT_HEADERS = [
    "Summary",
    "Scope",
    "Technical Design",
    "Files to Change",
    "Implementation Steps",
    "Validation Plan",
    "Rollback Plan"
]

def validate_blueprint_file(filepath: str, workflow_prefix: str = None) -> dict:
    if not os.path.exists(filepath):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Blueprint file does not exist at {filepath}.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }
        
    normalized = filepath.replace("\\", "/")
    
    # Path constraint checks
    if not normalized.startswith("docs/designs/"):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint file must be located under docs/designs/ directory.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    if not normalized.endswith("_blueprint.md"):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint filename must end with '_blueprint.md'.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    # Read content
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Failed to read file: {e}",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    # Validate YAML Frontmatter
    parts = content.split("---")
    if len(parts) < 3:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint must contain YAML frontmatter surrounded by '---'.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    frontmatter_raw = parts[1].strip()
    try:
        frontmatter = yaml.safe_load(frontmatter_raw)
    except Exception as e:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Invalid YAML frontmatter format: {e}",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    if not isinstance(frontmatter, dict):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Frontmatter is not a valid YAML dictionary.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    # Prefix matches check
    feat_id = frontmatter.get("feature_id", "")
    if workflow_prefix:
        if not feat_id.startswith(workflow_prefix):
            return {
                "status": "failure",
                "command": "validate blueprint",
                "summary": f"Blueprint feature_id '{feat_id}' does not match expected prefix '{workflow_prefix}'.",
                "warnings": [],
                "files_read": [filepath],
                "files_written": []
            }
            
    # Check headers
    missing_headers = []
    lines = content.splitlines()
    for header in REQUIRED_BLUEPRINT_HEADERS:
        found = False
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("#") and header.lower() in trimmed.lower():
                found = True
                break
        if not found:
            missing_headers.append(header)
            
    if missing_headers:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Blueprint is missing required headers: {', '.join(missing_headers)}.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }
        
    return {
        "status": "success",
        "command": "validate blueprint",
        "summary": "Blueprint file conforms to all standards.",
        "warnings": [],
        "files_read": [filepath],
        "files_written": []
    }

def validate_artifact_general(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {
            "status": "failure",
            "command": "validate artifact",
            "summary": f"Artifact file does not exist at {filepath}.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }
    return {
        "status": "success",
        "command": "validate artifact",
        "summary": f"Artifact file {filepath} verified.",
        "warnings": [],
        "files_read": [filepath],
        "files_written": []
    }
