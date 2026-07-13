# validate_registry.py
import os
import sys
import json
import shutil
from typing import Dict, List, Tuple, Any

def parse_yaml_frontmatter(yaml_str: str) -> dict:
    lines = yaml_str.split("\n")
    
    def parse_lines(line_idx: int, current_indent: int) -> Tuple[Any, int]:
        res = {}
        idx = line_idx
        while idx < len(lines):
            line = lines[idx]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                idx += 1
                continue
                
            # Get indent level
            indent = len(line) - len(line.lstrip(' '))
            if indent < current_indent:
                break
                
            if stripped.startswith("-"):
                idx += 1
                continue
                
            if ":" in line:
                parts = line.split(":", 1)
                k = parts[0].strip().strip('"').strip("'")
                v = parts[1].strip()
                
                next_idx = idx + 1
                is_nested = False
                is_list = False
                
                while next_idx < len(lines):
                    nl = lines[next_idx]
                    n_stripped = nl.strip()
                    if not n_stripped or n_stripped.startswith("#"):
                        next_idx += 1
                        continue
                    n_indent = len(nl) - len(nl.lstrip(' '))
                    if n_indent > indent:
                        if n_stripped.startswith("-"):
                            is_list = True
                        else:
                            is_nested = True
                    break
                    
                if is_list:
                    list_val = []
                    idx = next_idx
                    while idx < len(lines):
                        nl = lines[idx]
                        n_stripped = nl.strip()
                        if not n_stripped or n_stripped.startswith("#"):
                            idx += 1
                            continue
                        n_indent = len(nl) - len(nl.lstrip(' '))
                        if n_indent <= indent:
                            break
                        if n_stripped.startswith("-"):
                            val = n_stripped[1:].strip().strip('"').strip("'")
                            list_val.append(val)
                        idx += 1
                    res[k] = list_val
                elif is_nested:
                    nested_val, next_i = parse_lines(next_idx, indent + 1)
                    res[k] = nested_val
                    idx = next_i
                else:
                    # Scalar value
                    if v == "[]":
                        res[k] = []
                    elif v == "{}":
                        res[k] = {}
                    elif v == "" or v == "null":
                        res[k] = None
                    elif v.lower() == "true":
                        res[k] = True
                    elif v.lower() == "false":
                        res[k] = False
                    elif v.isdigit():
                        res[k] = int(v)
                    else:
                        try:
                            res[k] = float(v)
                        except ValueError:
                            res[k] = v.strip('"').strip("'")
                    idx += 1
            else:
                idx += 1
        return res, idx

    res, _ = parse_lines(0, 0)
    return res

CANONICAL_CAPABILITIES = {
    "brainstorming", "planning", "architecture", "frontend", "backend",
    "database", "testing", "verification", "review", "security", "release",
    "integration", "runtime", "observability", "performance", "accessibility",
    "documentation"
}

def load_schema(schema_path: str) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def custom_validate(instance: Any, schema: dict, path: str = "") -> List[str]:
    errors = []
    
    # 1. Check type
    schema_type = schema.get("type")
    if schema_type == "OBJECT":
        if not isinstance(instance, dict):
            errors.append(f"Field '{path}' must be an object/dict")
            return errors
        # Check required fields
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"Required field '{req}' is missing in '{path or 'root'}'")
        # Validate properties
        properties = schema.get("properties", {})
        for k, v in instance.items():
            if k in properties:
                errors.extend(custom_validate(v, properties[k], f"{path}.{k}" if path else k))
            elif schema.get("additionalProperties") is False:
                errors.append(f"Additional property '{k}' is not allowed in '{path or 'root'}'")
                
    elif schema_type == "ARRAY":
        if not isinstance(instance, (list, tuple)):
            errors.append(f"Field '{path}' must be an array/list")
            return errors
        item_schema = schema.get("items", {})
        for idx, item in enumerate(instance):
            errors.extend(custom_validate(item, item_schema, f"{path}[{idx}]"))
            
    elif schema_type == "STRING":
        if not isinstance(instance, str):
            errors.append(f"Field '{path}' must be a string")
        elif "enum" in schema:
            if instance not in schema["enum"]:
                errors.append(f"Field '{path}' value '{instance}' must be one of {schema['enum']}")
                
    elif schema_type == "NUMBER" or schema_type == "INTEGER":
        if not isinstance(instance, (int, float)) or (schema_type == "INTEGER" and not isinstance(instance, int)):
            errors.append(f"Field '{path}' must be a number/integer")
            
    elif schema_type == "BOOLEAN":
        if not isinstance(instance, bool):
            errors.append(f"Field '{path}' must be a boolean")
            
    return errors

def validate_agent(meta: dict, schema: dict, filename: str) -> List[str]:
    errors = []
    
    # Validate against schema
    errors.extend(custom_validate(meta, schema))
    
    # Validate capabilities
    caps = meta.get("capabilities", [])
    for cap in caps:
        if cap not in CANONICAL_CAPABILITIES:
            errors.append(f"[{filename}] Unsupported capability '{cap}'. Must be one of: {list(CANONICAL_CAPABILITIES)}")
            
    return errors

def main(workspace_root: str = ".") -> int:
    agents_dir = os.path.join(workspace_root, "agents")
    schema_path = os.path.join(agents_dir, "agent.schema.json")
    registry_path = os.path.join(agents_dir, "registry.json")
    
    if not os.path.exists(schema_path):
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        return 1
        
    schema = load_schema(schema_path)
    
    agent_files = []
    for fn in os.listdir(agents_dir):
        if fn.endswith(".md") and fn != "README.md":
            agent_files.append(fn)
            
    registry = {"agents": {}}
    all_errors = []
    
    agent_ids = set()
    role_owners = {} # role -> filename
    handoffs = {} # id -> handoff_targets
    
    print(f"Found {len(agent_files)} agent definitions in {agents_dir}...")
    
    # 1. Parse and validate each file
    for fn in sorted(agent_files):
        fp = os.path.join(agents_dir, fn)
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            all_errors.append(f"Failed to read file {fn}: {e}")
            continue
            
        if not content.startswith("---"):
            all_errors.append(f"File {fn} does not start with frontmatter markers '---'")
            continue
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            all_errors.append(f"File {fn} has invalid frontmatter structure")
            continue
            
        try:
            meta = parse_yaml_frontmatter(parts[1])
        except Exception as e:
            all_errors.append(f"Syntax error in custom frontmatter parser for {fn}: {e}")
            continue
            
        if not isinstance(meta, dict):
            all_errors.append(f"Frontmatter of {fn} must be a dictionary")
            continue
            
        errors = validate_agent(meta, schema, fn)
        if errors:
            for err in errors:
                all_errors.append(f"[{fn}] {err}")
            continue
            
        agent_id = meta.get("id")
        
        # Check duplicate ID
        if agent_id in agent_ids:
            all_errors.append(f"[{fn}] Duplicate agent ID: {agent_id}")
        agent_ids.add(agent_id)
        
        # Check duplicate canonical role ownership
        role = meta.get("role")
        if role:
            if role in ["planner", "architect", "release-manager", "main-orchestrator"]:
                if role in role_owners:
                    all_errors.append(f"[{fn}] Duplicate ownership of canonical role '{role}'. Already owned by {role_owners[role]}.")
                role_owners[role] = fn
                
        # Register handoffs
        handoffs[agent_id] = meta.get("handoff_targets", [])
        
        registry["agents"][agent_id] = meta
        
    # 2. Validate Handoff targets existence
    for aid, targets in handoffs.items():
        for target in targets:
            if target != "done" and target not in agent_ids:
                all_errors.append(f"Agent '{aid}' declares handoff target '{target}' which does not exist in registry.")
                
    # 3. Output results
    if all_errors:
        print("\n❌ Validation failed with errors:")
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
        
    # Write registry.json
    try:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        print(f"✔ Registry compiled successfully: {registry_path}")
    except Exception as e:
        print(f"Error writing registry: {e}", file=sys.stderr)
        return 1
        
    # 4. Sync to .agents/agents/
    dest_dir = os.path.join(workspace_root, ".agents", "agents")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Sync registry.json
    shutil.copy(registry_path, os.path.join(dest_dir, "registry.json"))
    shutil.copy(schema_path, os.path.join(dest_dir, "agent.schema.json"))
    
    # Sync md files
    for fn in agent_files:
        shutil.copy(os.path.join(agents_dir, fn), os.path.join(dest_dir, fn))
        
    print(f"✔ Synced registry and agent files to: {dest_dir}")
    
    # 5. Generate Audit Report
    report_dir = os.path.join(workspace_root, "docs", "debug")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "agent_registry_audit_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Agent Registry Audit Report\n\n")
        f.write(f"- **Total Agents Discovered**: {len(agent_files)}\n")
        f.write(f"- **Valid Agents**: {len(registry['agents'])}\n")
        f.write(f"- **Invalid Agents**: 0\n")
        f.write("- **Duplicate Roles**: None\n")
        f.write(f"- **Registered IDs**: {', '.join(sorted(agent_ids))}\n")
        
    print(f"✔ Audit report generated: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
