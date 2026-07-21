import os
import json
import stat
import warnings
import urllib.request
import socket
import re

MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)

def translate_links_to_wikilinks(content: str) -> str:
    """Convert standard Markdown links and absolute file:// links targeting .md files to [[wikilinks]]."""
    def repl(match):
        label = match.group(1)
        url = match.group(2)
        
        clean_url = url
        if clean_url.startswith('file://'):
            clean_url = clean_url[7:]
            
        # Clean relative anchor paths
        clean_url = clean_url.split('#')[0]
        
        if clean_url.endswith('.md'):
            basename = os.path.basename(clean_url)
            note_name = os.path.splitext(basename)[0]
            
            if label.strip().lower() == note_name.strip().lower() or label.strip() == basename:
                return f"[[{note_name}]]"
            else:
                return f"[[{note_name}|{label}]]"
        return match.group(0)
        
    return MARKDOWN_LINK_PATTERN.sub(repl, content)

def translate_wikilinks_to_markdown(content: str) -> str:
    """Convert Obsidian [[wikilinks]] back to standard Markdown links or text."""
    def repl(match):
        note_name = match.group(1).strip()
        label = match.group(2)
        
        display_label = label.strip() if label else note_name
        # Render as a markdown link pointing to the simulated .md format
        return f"[{display_label}]({note_name}.md)"
        
    return WIKILINK_PATTERN.sub(repl, content)

def merge_frontmatter(content: str, metadata: dict) -> str:
    """Safely inject or merge YAML frontmatter fields at the top of markdown content."""
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        original_frontmatter = match.group(1)
        body = content[match.end():]
        
        # Simple line parsing
        front_dict = {}
        for line in original_frontmatter.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                front_dict[k.strip()] = v.strip()
                
        # Merge new metadata
        for k, v in metadata.items():
            front_dict[k] = str(v)
            
        # Reconstruct frontmatter
        new_front = "---\n"
        for k, v in front_dict.items():
            new_front += f"{k}: {v}\n"
        new_front += "---\n"
        return new_front + body
    else:
        new_front = "---\n"
        for k, v in metadata.items():
            new_front += f"{k}: {v}\n"
        new_front += "---\n"
        return new_front + content

def clean_frontmatter(content: str) -> str:
    """Remove only the added sync fields from YAML frontmatter, keeping the rest."""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return content
    original_frontmatter = match.group(1)
    body = content[match.end():]
    
    front_dict = {}
    for line in original_frontmatter.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            front_dict[k.strip()] = v.strip()
            
    # Remove added fields
    for k in ["sync_date", "source_path", "type"]:
        front_dict.pop(k, None)
        
    if not front_dict:
        return body
        
    new_front = "---\n"
    for k, v in front_dict.items():
        new_front += f"{k}: {v}\n"
    new_front += "---\n"
    return new_front + body

def get_global_config_path() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, ".aiwf", "providers.json")

def load_global_config() -> dict:
    path = get_global_config_path()
    if not os.path.exists(path):
        # Ensure directory exists with 0o700
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            try:
                os.chmod(dir_path, 0o700)
            except Exception:
                pass
        return {"providers": {}}
        
    # Check permissions
    try:
        st = os.stat(path)
        if os.name != 'nt':
            if (st.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) != 0:
                warnings.warn(f"Security Warning: Global provider config permissions at {path} are too broad. Recommended: chmod 600.")
    except Exception:
        pass
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        warnings.warn(f"Failed to read global config: {e}")
        return {"providers": {}}

def save_global_config(config: dict) -> bool:
    path = get_global_config_path()
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        try:
            os.chmod(dir_path, 0o700)
        except Exception:
            pass
            
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        if os.name != 'nt':
            try:
                os.chmod(path, 0o600)
            except Exception:
                pass
        return True
    except Exception as e:
        warnings.warn(f"Failed to save global config: {e}")
        return False

def load_project_config(project_root: str = ".") -> dict:
    if not project_root:
        project_root = "."
    path = os.path.join(project_root, ".agents", "memory.config.json")
    if not os.path.exists(path):
        return {"providers": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        warnings.warn(f"Failed to read project config: {e}")
        return {"providers": {}}

def resolve_env_vars(val):
    if isinstance(val, str):
        return os.path.expandvars(val)
    elif isinstance(val, dict):
        return {k: resolve_env_vars(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [resolve_env_vars(v) for v in val]
    return val

def resolve_provider_config(name: str, project_root: str = ".") -> dict:
    global_cfg = load_global_config().get("providers", {}).get(name, {})
    project_cfg = load_project_config(project_root).get("providers", {}).get(name, {})
    
    # Merge project overrides on top of global config
    merged = {}
    merged.update(global_cfg)
    merged.update(project_cfg)
    
    # Resolve env variables
    return resolve_env_vars(merged)

def resolve_all_providers(project_root: str = ".") -> dict:
    global_cfg = load_global_config().get("providers", {})
    project_cfg = load_project_config(project_root).get("providers", {})
    
    all_names = set(list(global_cfg.keys()) + list(project_cfg.keys()))
    resolved = {}
    for name in all_names:
        resolved[name] = resolve_provider_config(name, project_root)
        
    return {"providers": resolved}

def list_providers(project_root: str = ".") -> dict:
    providers = resolve_all_providers(project_root).get("providers", {})
    return mask_secrets(providers)

def enable_provider(name: str) -> bool:
    config = load_global_config()
    if "providers" not in config:
        config["providers"] = {}
    if name not in config["providers"]:
        config["providers"][name] = {}
    config["providers"][name]["enabled"] = True
    return save_global_config(config)

def disable_provider(name: str) -> bool:
    config = load_global_config()
    if "providers" not in config:
        config["providers"] = {}
    if name not in config["providers"]:
        config["providers"][name] = {}
    config["providers"][name]["enabled"] = False
    return save_global_config(config)

def mask_secrets(config):
    if not isinstance(config, dict):
        return config
    masked = {}
    for k, v in config.items():
        if isinstance(v, dict):
            masked[k] = mask_secrets(v)
        elif isinstance(v, list):
            masked[k] = [mask_secrets(item) if isinstance(item, dict) else item for item in v]
        elif isinstance(v, str) and any(sec in k.lower() for sec in ["key", "token", "password", "secret"]):
            masked[k] = "********" if v else ""
        else:
            masked[k] = v
    return masked

def test_provider(name: str, project_root: str = ".") -> dict:
    cfg = resolve_provider_config(name, project_root)
    if not cfg:
        return {"status": "failure", "message": f"Provider {name} is not configured."}
        
    if not cfg.get("enabled", False):
        return {"status": "failure", "message": f"Provider {name} is disabled."}
        
    if name == "obsidian":
        try:
            path = resolve_obsidian_project_folder(project_root)
        except Exception as e:
            return {"status": "failure", "message": f"Obsidian folder resolution failed: {e}"}
            
        mode = cfg.get("mode", "file-sync")
        if mode in ["file-sync", "readonly", "bidirectional"]:
            if os.path.exists(path) and os.path.isdir(path):
                return {"status": "success", "message": f"Obsidian {mode} mode verified: vault exists at {path}."}
            return {"status": "failure", "message": f"Obsidian vault folder does not exist: {path}."}
        elif mode == "rest":
            host = cfg.get("host", "127.0.0.1")
            port = cfg.get("port", 27124)
            token = cfg.get("api_key", "")
            url = f"http://{host}:{port}"
            try:
                req = urllib.request.Request(f"{url}/", method="GET")
                if token:
                    req.add_header("Authorization", f"Bearer {token}")
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    if response.status == 200:
                        return {"status": "success", "message": "Obsidian REST API verified successfully."}
            except Exception as e:
                return {"status": "failure", "message": f"Failed to connect to Obsidian REST API: {e}"}
            
    elif name == "qdrant":
        host = cfg.get("host", "127.0.0.1")
        port = cfg.get("port", 6333)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            res = sock.connect_ex((host, int(port)))
            sock.close()
            if res == 0:
                return {"status": "success", "message": f"Connected to Qdrant successfully at {host}:{port}."}
            return {"status": "failure", "message": f"Failed to connect to Qdrant at {host}:{port}."}
        except Exception as e:
            return {"status": "failure", "message": f"Qdrant connection error: {e}"}
            
    elif name == "openai":
        api_key = cfg.get("api_key", "")
        if api_key:
            return {"status": "success", "message": "OpenAI provider API Key configured."}
        return {"status": "failure", "message": "OpenAI provider API Key is missing."}
        
    return {"status": "success", "message": f"Provider {name} configuration checked."}

def resolve_obsidian_project_folder(project_root: str = ".") -> str:
    if not project_root:
        project_root = "."
    obs_cfg = resolve_provider_config("obsidian", project_root)
    if not obs_cfg:
        raise ValueError("Obsidian provider is not configured.")
        
    vault_root = obs_cfg.get("vault_root", "")
    vault_path = obs_cfg.get("vault_path", "")
    if vault_path and not vault_root:
        vault_root = vault_path
        warnings.warn("Obsidian Configuration Warning: 'vault_path' is deprecated. Please migrate to 'vault_root'.")
        
    if not vault_root:
        raise ValueError("Obsidian vault_root is empty or not configured.")
        
    vault_root = os.path.abspath(os.path.expanduser(vault_root))
    map_dir = os.path.join(project_root, ".agents", "knowledge")
    map_path = os.path.join(map_dir, "obsidian-project-map.json")
    
    project_id = ""
    try:
        proj_cfg = load_project_config(project_root)
        project_id = proj_cfg.get("project_id", "")
    except Exception:
        pass
        
    if not project_id:
        try:
            prof_path = os.path.join(project_root, ".agents", "project-profile.json")
            if os.path.exists(prof_path):
                with open(prof_path, "r", encoding="utf-8") as f:
                    prof = json.load(f)
                    project_id = prof.get("name", "") or prof.get("id", "")
        except Exception:
            pass
            
    if not project_id:
        try:
            import subprocess
            git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=os.path.abspath(project_root)).decode().strip()
            project_id = os.path.basename(git_root)
        except Exception:
            pass
            
    if not project_id:
        project_id = os.path.basename(os.path.abspath(project_root))
        
    import re
    clean_id = project_id.replace(" ", "-")
    clean_id = re.sub(r'[^a-zA-Z0-9\-_.]', '', clean_id)
    clean_id = re.sub(r'-+', '-', clean_id)
    clean_id = re.sub(r'_+', '_', clean_id)
    clean_id = clean_id.strip('-').strip('_')
    
    parts = re.split(r'([\-_.])', clean_id)
    formatted_parts = []
    for part in parts:
        if part in ['-', '_', '.']:
            formatted_parts.append(part)
        else:
            if part.lower() == 'ai':
                formatted_parts.append('AI')
            elif part.lower() == 'aiwf':
                formatted_parts.append('AIWF')
            else:
                formatted_parts.append(part.capitalize())
    project_slug = "".join(formatted_parts)
    
    mapping = {}
    if os.path.exists(map_path):
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except Exception:
            pass
            
    if mapping:
        vault_folder = mapping.get("vault_folder", "")
        resolved_path = os.path.abspath(os.path.join(vault_root, vault_folder))
    else:
        pattern = obs_cfg.get("project_folder_pattern", "AIWF-Knowledge-{project_slug}")
        vault_folder = pattern.replace("{project_slug}", project_slug)
        if "/" in vault_folder or "\\" in vault_folder or ".." in vault_folder:
            raise ValueError(f"Path traversal detected in project_folder_pattern or resolved vault_folder: {vault_folder}")
        resolved_path = os.path.abspath(os.path.join(vault_root, vault_folder))
        
    try:
        common = os.path.commonpath([vault_root, resolved_path])
        if common != vault_root:
            raise ValueError("Security Violation: Resolved Obsidian path must be inside vault_root.")
    except Exception as e:
        raise ValueError(f"Security Violation: Path validation failed: {e}")
        
    readme_path = os.path.join(resolved_path, "README.md")
    if os.path.exists(resolved_path):
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
                slug_match = re.search(r'Project Slug:\s*([^\n\r]+)', readme_content)
                if slug_match:
                    existing_slug = slug_match.group(1).strip()
                    if existing_slug != project_slug:
                        raise ValueError(f"Conflict: Obsidian folder '{vault_folder}' belongs to another project (slug: {existing_slug}).")
            except ValueError as ve:
                raise ve
            except Exception:
                pass
                
    create_if_missing = obs_cfg.get("create_if_missing", True)
    sync_structure = obs_cfg.get("sync_structure", True)
    
    import datetime
    now_iso = datetime.datetime.now().astimezone().isoformat()
    
    if not os.path.exists(resolved_path) and create_if_missing:
        os.makedirs(resolved_path, exist_ok=True)
        
    if os.path.exists(resolved_path) and sync_structure:
        folder_mapping = obs_cfg.get("folder_mapping", {
            "docs/brainstorming": "Brainstorming",
            "docs/plans": "Plans",
            "docs/blueprints": "Blueprints",
            "docs/adr": "ADR",
            "docs/releases": "Releases",
            ".agents/memory": "Memory",
            "lessons": "Lessons",
            "patterns": "Patterns"
        })
        subdirs = ["Assets", "Indexes"]
        for obs_dir in folder_mapping.values():
            if obs_dir not in subdirs:
                subdirs.append(obs_dir)
        for sd in subdirs:
            os.makedirs(os.path.join(resolved_path, sd), exist_ok=True)
            
        if not os.path.exists(readme_path):
            masked_cfg = mask_secrets(obs_cfg)
            readme_content = f"""# Obsidian Knowledge Vault - {project_id}

This is the automatically managed Obsidian knowledge folder for project **{project_id}**.

## Project Metadata
- **Project Name**: {project_id}
- **Project Slug**: {project_slug}
- **AIWF Project Path**: {os.path.abspath(project_root)}
- **Last Sync Time**: {now_iso}
- **Sync Mode**: {obs_cfg.get("mode", "file-sync")}

## Configuration Summary
```json
{json.dumps(masked_cfg, indent=2)}
```

## Folder Structure Links
- [[Brainstorming/README|Brainstorming]]
- [[Plans/README|Plans]]
- [[Blueprints/README|Blueprints]]
- [[ADR/README|ADR]]
- [[Memory/README|Memory]]
- [[Releases/README|Releases]]
- [[Lessons/README|Lessons]]
- [[Patterns/README|Patterns]]
"""
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
                
    os.makedirs(map_dir, exist_ok=True)
    new_mapping = {
        "project_id": project_id,
        "project_slug": project_slug,
        "vault_root": vault_root,
        "vault_folder": vault_folder,
        "resolved_path": resolved_path,
        "created_at": mapping.get("created_at", now_iso),
        "updated_at": now_iso
    }
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(new_mapping, f, indent=2)
        
    return resolved_path

def get_file_hash(path: str) -> str:
    if not os.path.exists(path):
        return ""
    import hashlib
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception:
        return ""

def sync_obsidian(project_root: str = ".") -> dict:
    if not project_root:
        project_root = "."
    obs_cfg = resolve_provider_config("obsidian", project_root)
    if not obs_cfg:
        return {"status": "failure", "message": "Obsidian is not configured."}
        
    if not obs_cfg.get("enabled", False):
        return {"status": "failure", "message": "Obsidian provider is disabled."}
        
    mode = obs_cfg.get("mode", "file-sync")
    
    try:
        resolved_path = resolve_obsidian_project_folder(project_root)
    except Exception as e:
        return {"status": "failure", "message": f"Folder resolution failed: {e}"}
        
    folder_mapping = obs_cfg.get("folder_mapping", {
        "docs/brainstorming": "Brainstorming",
        "docs/plans": "Plans",
        "docs/quick": "Brainstorming",
        "docs/issues": "Plans",
        "docs/blueprints": "Blueprints",
        "docs/adr": "ADR",
        "docs/releases": "Releases",
        ".agents/memory": "Memory",
        "lessons": "Lessons",
        "patterns": "Patterns",
        "docs/prompts": "Prompts",
        "docs/verification": "Verification",
        "docs/debug": "Debug",
        "docs/archive": "Archive"
    })
    
    sync_map_dir = os.path.join(project_root, ".agents", "knowledge")
    sync_map_path = os.path.join(sync_map_dir, "obsidian-sync-map.json")
    sync_map = {}
    if os.path.exists(sync_map_path):
        try:
            with open(sync_map_path, "r", encoding="utf-8") as f:
                sync_map = json.load(f)
        except Exception:
            pass
            
    stats = {
        "copied_to_obsidian": [],
        "copied_to_aiwf": [],
        "skipped_readonly": [],
        "conflicts": [],
        "errors": []
    }
    
    import datetime
    now_iso = datetime.datetime.now().astimezone().isoformat()
    
    for aiwf_folder, obs_folder in folder_mapping.items():
        aiwf_full_dir = os.path.abspath(os.path.join(project_root, aiwf_folder))
        obs_full_dir = os.path.abspath(os.path.join(resolved_path, obs_folder))
        
        if not os.path.exists(aiwf_full_dir):
            continue
            
        os.makedirs(obs_full_dir, exist_ok=True)
        
        for root, _, files in os.walk(aiwf_full_dir):
            for filename in files:
                if filename.startswith(".") or filename.endswith(".lock") or filename.endswith("~"):
                    continue
                
                aiwf_file = os.path.join(root, filename)
                rel_path = os.path.relpath(aiwf_file, aiwf_full_dir)
                obs_file = os.path.join(obs_full_dir, rel_path)
                
                rel_to_proj_aiwf = os.path.relpath(aiwf_file, os.path.abspath(project_root))
                rel_to_obs_root = os.path.relpath(obs_file, os.path.abspath(resolved_path))
                
                aiwf_hash = get_file_hash(aiwf_file)
                obs_hash = get_file_hash(obs_file) if os.path.exists(obs_file) else ""
                
                entry = sync_map.get(rel_to_proj_aiwf, {
                    "aiwf_path": rel_to_proj_aiwf,
                    "obsidian_path": rel_to_obs_root,
                    "last_aiwf_hash": "",
                    "last_obsidian_hash": "",
                    "last_synced_at": ""
                })
                
                last_aiwf_hash = entry.get("last_aiwf_hash", "")
                last_obsidian_hash = entry.get("last_obsidian_hash", "")
                
                aiwf_changed = (aiwf_hash != last_aiwf_hash)
                obs_changed = (obs_hash != last_obsidian_hash) and os.path.exists(obs_file)
                
                if mode == "readonly":
                    if aiwf_changed:
                        stats["skipped_readonly"].append(rel_to_proj_aiwf)
                    continue
                    
                elif mode in ["file-sync", "rest"]:
                    if aiwf_changed or not os.path.exists(obs_file):
                        try:
                            os.makedirs(os.path.dirname(obs_file), exist_ok=True)
                            if filename.endswith(".md"):
                                with open(aiwf_file, "r", encoding="utf-8") as f:
                                    content = f.read()
                                translated = translate_links_to_wikilinks(content)
                                meta = {
                                    "sync_date": now_iso,
                                    "source_path": rel_to_proj_aiwf.replace(os.sep, '/'),
                                    "type": obs_folder.lower()
                                }
                                final_content = merge_frontmatter(translated, meta)
                                with open(obs_file, "w", encoding="utf-8") as f:
                                    f.write(final_content)
                            else:
                                import shutil
                                shutil.copy2(aiwf_file, obs_file)
                            obs_hash = get_file_hash(obs_file)
                            sync_map[rel_to_proj_aiwf] = {
                                "aiwf_path": rel_to_proj_aiwf,
                                "obsidian_path": rel_to_obs_root,
                                "last_aiwf_hash": aiwf_hash,
                                "last_obsidian_hash": obs_hash,
                                "last_synced_at": now_iso
                            }
                            stats["copied_to_obsidian"].append(rel_to_proj_aiwf)
                        except Exception as e:
                            stats["errors"].append(f"Failed to copy {rel_to_proj_aiwf} to Obsidian: {e}")
                            
                elif mode == "bidirectional":
                    if aiwf_changed and obs_changed:
                        stats["conflicts"].append(rel_to_proj_aiwf)
                        conflict_dir = os.path.join(project_root, ".agents", "knowledge", "conflicts")
                        os.makedirs(conflict_dir, exist_ok=True)
                        safe_conflict_name = rel_to_proj_aiwf.replace("/", "_").replace("\\", "_") + ".json"
                        conflict_path = os.path.join(conflict_dir, safe_conflict_name)
                        conflict_report = {
                            "aiwf_path": rel_to_proj_aiwf,
                            "obsidian_path": rel_to_obs_root,
                            "last_synced_at": entry.get("last_synced_at", ""),
                            "aiwf_current_hash": aiwf_hash,
                            "obsidian_current_hash": obs_hash,
                            "detected_at": now_iso
                        }
                        try:
                            with open(conflict_path, "w", encoding="utf-8") as cf:
                                json.dump(conflict_report, cf, indent=2)
                        except Exception:
                            pass
                    elif aiwf_changed:
                        try:
                            os.makedirs(os.path.dirname(obs_file), exist_ok=True)
                            if filename.endswith(".md"):
                                with open(aiwf_file, "r", encoding="utf-8") as f:
                                    content = f.read()
                                translated = translate_links_to_wikilinks(content)
                                meta = {
                                    "sync_date": now_iso,
                                    "source_path": rel_to_proj_aiwf.replace(os.sep, '/'),
                                    "type": obs_folder.lower()
                                }
                                final_content = merge_frontmatter(translated, meta)
                                with open(obs_file, "w", encoding="utf-8") as f:
                                    f.write(final_content)
                            else:
                                import shutil
                                shutil.copy2(aiwf_file, obs_file)
                            obs_hash = get_file_hash(obs_file)
                            sync_map[rel_to_proj_aiwf] = {
                                "aiwf_path": rel_to_proj_aiwf,
                                "obsidian_path": rel_to_obs_root,
                                "last_aiwf_hash": aiwf_hash,
                                "last_obsidian_hash": obs_hash,
                                "last_synced_at": now_iso
                            }
                            stats["copied_to_obsidian"].append(rel_to_proj_aiwf)
                        except Exception as e:
                            stats["errors"].append(f"Failed to copy {rel_to_proj_aiwf} to Obsidian: {e}")
                    elif obs_changed:
                        try:
                            os.makedirs(os.path.dirname(aiwf_file), exist_ok=True)
                            if filename.endswith(".md"):
                                with open(obs_file, "r", encoding="utf-8") as f:
                                    content = f.read()
                                translated = translate_wikilinks_to_markdown(content)
                                final_content = clean_frontmatter(translated)
                                with open(aiwf_file, "w", encoding="utf-8") as f:
                                    f.write(final_content)
                            else:
                                import shutil
                                shutil.copy2(obs_file, aiwf_file)
                            aiwf_hash = get_file_hash(aiwf_file)
                            sync_map[rel_to_proj_aiwf] = {
                                "aiwf_path": rel_to_proj_aiwf,
                                "obsidian_path": rel_to_obs_root,
                                "last_aiwf_hash": aiwf_hash,
                                "last_obsidian_hash": obs_hash,
                                "last_synced_at": now_iso
                            }
                            stats["copied_to_aiwf"].append(rel_to_proj_aiwf)
                        except Exception as e:
                            stats["errors"].append(f"Failed to copy {rel_to_obs_root} from Obsidian: {e}")
                            
    os.makedirs(sync_map_dir, exist_ok=True)
    try:
        with open(sync_map_path, "w", encoding="utf-8") as f:
            json.dump(sync_map, f, indent=2)
    except Exception:
        pass
        
    return {
        "status": "success",
        "message": f"Sync completed with {len(stats['copied_to_obsidian'])} copied to Obsidian, {len(stats['copied_to_aiwf'])} copied to AIWF, {len(stats['conflicts'])} conflicts.",
        "stats": stats
    }
