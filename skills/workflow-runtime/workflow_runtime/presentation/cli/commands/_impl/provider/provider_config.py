"""Handler: do_provider_action part A."""
from __future__ import annotations

import os
import sys
from typing import Any, cast

from workflow_runtime.presentation.cli.commands._impl.provider.provider_data import \
    kill_all_telegram_processes
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    ForbiddenAISourceError, extract_work_item_id_from_text,
    get_current_project_context, is_telegram_daemon_running,
    sync_analysis_agents_to_session)


def _mask_provider_secrets(value: Any) -> Any:
    secret_keys = ("token", "key", "secret", "password", "credential")
    if isinstance(value, dict):
        val_dict = cast(dict[str, Any], value)
        masked: dict[str, Any] = {}
        for key, item in val_dict.items():
            if any(secret in str(key).lower() for secret in secret_keys):
                masked[key] = "***" if item else item
            else:
                masked[key] = _mask_provider_secrets(item)
        return masked
    if isinstance(value, list):
        val_list = cast(list[Any], value)
        return [_mask_provider_secrets(item) for item in val_list]
    return value
    return value

def do_provider_action(args: Any):
    import json
    import os

    from workflow_runtime.application.knowledge.knowledge_provider_factory import \
        KnowledgeProviderFactory
    provider_manager = cast(Any, KnowledgeProviderFactory)

    "." if getattr(args, "project", False) else None

    if (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "path":
        print(provider_manager.get_global_config_path())
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "list":
        if getattr(args, "project", False):
            res = provider_manager.list_providers(project_root=".")
        else:
            res = _mask_provider_secrets(provider_manager.load_global_config().get("providers", {}))
        print(json.dumps(res, indent=2))
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "add":
        name = args.name
        if name == "obsidian":
            vault_root = input("Enter vault_root (absolute path to your Obsidian vault): ").strip()
            pattern = input("Enter project_folder_pattern [AIWF-Knowledge-{project_slug}]: ").strip() or "AIWF-Knowledge-{project_slug}"
            mode = input("Enter mode (file-sync | rest | readonly | bidirectional) [file-sync]: ").strip() or "file-sync"
            create_if_missing_in = input("Create if missing? (y/n) [y]: ").strip().lower() or "y"
            create_if_missing = (create_if_missing_in == "y")
            sync_structure_in = input("Sync structure? (y/n) [y]: ").strip().lower() or "y"
            sync_structure = (sync_structure_in == "y")

            host = "127.0.0.1"
            port = 27124
            api_key = ""
            if mode in ["rest", "bidirectional"]:
                host = input("Enter host [127.0.0.1]: ").strip() or "127.0.0.1"
                port_in = input("Enter port [27124]: ").strip() or "27124"
                port = int(port_in) if port_in.isdigit() else 27124
                import getpass
                api_key = getpass.getpass("Enter API Key or environment variable name: ").strip()

            prov_cfg = {
                "enabled": True,
                "mode": mode,
                "vault_root": vault_root,
                "project_folder_pattern": pattern,
                "create_if_missing": create_if_missing,
                "sync_structure": sync_structure,
                "host": host,
                "port": port,
                "api_key": api_key
            }
        else:
            mode = input("Enter mode (file-sync | rest | readonly | bidirectional) [file-sync]: ").strip() or "file-sync"
            host = input("Enter host [127.0.0.1]: ").strip() or "127.0.0.1"
            port_in = input("Enter port [27124]: ").strip() or "27124"
            port = int(port_in) if port_in.isdigit() else 27124

            import getpass
            api_key = getpass.getpass("Enter API Key or environment variable name: ").strip()
            vault_path = input("Enter vault path: ").strip()

            prov_cfg = {
                "enabled": True,
                "mode": mode,
                "host": host,
                "port": port,
                "api_key": api_key,
                "vault_path": vault_path
            }

        if getattr(args, "project", False):
            proj_cfg = provider_manager.load_project_config(".")
            if "providers" not in proj_cfg:
                proj_cfg["providers"] = {}
            proj_cfg["providers"][name] = prov_cfg
            proj_cfg_path = os.path.join(".", ".agents", "memory.config.json")
            os.makedirs(os.path.dirname(proj_cfg_path), exist_ok=True)
            with open(proj_cfg_path, "w", encoding="utf-8") as f:
                json.dump(proj_cfg, f, indent=2)
            print(f"Added provider {name} to project configuration successfully.")
        else:
            global_cfg = provider_manager.load_global_config()
            if "providers" not in global_cfg:
                global_cfg["providers"] = {}
            global_cfg["providers"][name] = prov_cfg
            provider_manager.save_global_config(global_cfg)
            print(f"Added provider {name} to global configuration successfully.")
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "edit":
        name = args.name
        if getattr(args, "project", False):
            existing = provider_manager.load_project_config(".").get("providers", {}).get(name, {})
        else:
            existing = provider_manager.load_global_config().get("providers", {}).get(name, {})

        print(f"Editing provider {name} (leave empty to keep current value):")
        if name == "obsidian":
            vault_root = input(f"Enter vault_root ({existing.get('vault_root', '')}): ").strip() or existing.get('vault_root', '')
            pattern = input(f"Enter project_folder_pattern ({existing.get('project_folder_pattern', 'AIWF-Knowledge-{project_slug}')}): ").strip() or existing.get('project_folder_pattern', 'AIWF-Knowledge-{project_slug}')
            mode = input(f"Enter mode ({existing.get('mode', 'file-sync')}): ").strip() or existing.get('mode', 'file-sync')

            create_if_missing_str = "y" if existing.get("create_if_missing", True) else "n"
            create_if_missing_in = input(f"Create if missing? (y/n) [{create_if_missing_str}]: ").strip().lower() or create_if_missing_str
            create_if_missing = (create_if_missing_in == "y")

            sync_structure_str = "y" if existing.get("sync_structure", True) else "n"
            sync_structure_in = input(f"Sync structure? (y/n) [{sync_structure_str}]: ").strip().lower() or sync_structure_str
            sync_structure = (sync_structure_in == "y")

            host = existing.get("host", "127.0.0.1")
            port = existing.get("port", 27124)
            api_key = existing.get("api_key", "")
            if mode in ["rest", "bidirectional"]:
                host = input(f"Enter host ({existing.get('host', '127.0.0.1')}): ").strip() or existing.get('host', '127.0.0.1')
                port_in = input(f"Enter port ({existing.get('port', 27124)}): ").strip()
                port = int(port_in) if port_in.isdigit() else existing.get('port', 27124)
                import getpass
                api_key = getpass.getpass("Enter API Key or environment variable name (masked): ").strip() or existing.get('api_key', '')

            prov_cfg = {
                "enabled": existing.get("enabled", True),
                "mode": mode,
                "vault_root": vault_root,
                "project_folder_pattern": pattern,
                "create_if_missing": create_if_missing,
                "sync_structure": sync_structure,
                "host": host,
                "port": port,
                "api_key": api_key
            }
        else:
            mode = input(f"Enter mode ({existing.get('mode', 'file-sync')}): ").strip() or existing.get('mode', 'file-sync')
            host = input(f"Enter host ({existing.get('host', '127.0.0.1')}): ").strip() or existing.get('host', '127.0.0.1')
            port_in = input(f"Enter port ({existing.get('port', 27124)}): ").strip()
            port = int(port_in) if port_in.isdigit() else existing.get('port', 27124)

            import getpass
            api_key = getpass.getpass("Enter API Key or environment variable name (masked): ").strip() or existing.get('api_key', '')
            vault_path = input(f"Enter vault path ({existing.get('vault_path', '')}): ").strip() or existing.get('vault_path', '')

            prov_cfg = {
                "enabled": existing.get("enabled", True),
                "mode": mode,
                "host": host,
                "port": port,
                "api_key": api_key,
                "vault_path": vault_path
            }

        if getattr(args, "project", False):
            proj_cfg = provider_manager.load_project_config(".")
            if "providers" not in proj_cfg:
                proj_cfg["providers"] = {}
            proj_cfg["providers"][name] = prov_cfg
            proj_cfg_path = os.path.join(".", ".agents", "memory.config.json")
            with open(proj_cfg_path, "w", encoding="utf-8") as f:
                json.dump(proj_cfg, f, indent=2)
            print(f"Edited provider {name} in project configuration successfully.")
        else:
            global_cfg = provider_manager.load_global_config()
            if "providers" not in global_cfg:
                global_cfg["providers"] = {}
            global_cfg["providers"][name] = prov_cfg
            provider_manager.save_global_config(global_cfg)
            print(f"Edited provider {name} in global configuration successfully.")
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "remove":
        name = args.name
        if getattr(args, "project", False):
            proj_cfg = provider_manager.load_project_config(".")
            if "providers" in proj_cfg and name in proj_cfg["providers"]:
                del proj_cfg["providers"][name]
                proj_cfg_path = os.path.join(".", ".agents", "memory.config.json")
                with open(proj_cfg_path, "w", encoding="utf-8") as f:
                    json.dump(proj_cfg, f, indent=2)
                print(f"Removed provider {name} from project configuration successfully.")
        else:
            global_cfg = provider_manager.load_global_config()
            if "providers" in global_cfg and name in global_cfg["providers"]:
                del global_cfg["providers"][name]
                provider_manager.save_global_config(global_cfg)
                print(f"Removed provider {name} from global configuration successfully.")
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "enable":
        name = args.name
        if getattr(args, "project", False):
            proj_cfg = provider_manager.load_project_config(".")
            if "providers" not in proj_cfg:
                proj_cfg["providers"] = {}
            if name not in proj_cfg["providers"]:
                proj_cfg["providers"][name] = {}
            proj_cfg["providers"][name]["enabled"] = True
            proj_cfg_path = os.path.join(".", ".agents", "memory.config.json")
            with open(proj_cfg_path, "w", encoding="utf-8") as f:
                json.dump(proj_cfg, f, indent=2)
            print(f"Enabled provider {name} in project configuration.")
        else:
            provider_manager.enable_provider(name)
            print(f"Enabled provider {name} in global configuration.")
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "disable":
        name = args.name
        if getattr(args, "project", False):
            proj_cfg = provider_manager.load_project_config(".")
            if "providers" not in proj_cfg:
                proj_cfg["providers"] = {}
            if name not in proj_cfg["providers"]:
                proj_cfg["providers"][name] = {}
            proj_cfg["providers"][name]["enabled"] = False
            proj_cfg_path = os.path.join(".", ".agents", "memory.config.json")
            with open(proj_cfg_path, "w", encoding="utf-8") as f:
                json.dump(proj_cfg, f, indent=2)
            print(f"Disabled provider {name} in project configuration.")
        else:
            provider_manager.disable_provider(name)
            print(f"Disabled provider {name} in global configuration.")
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "test":
        name = args.name
        res = provider_manager.test_provider(name, project_root="." if getattr(args, "project", False) else None)
        print(json.dumps(res, indent=2))
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "resolve":
        name = args.name
        if name == "obsidian":
            path = provider_manager.get_global_config_path()
            try:
                resolved_folder = provider_manager.resolve_obsidian_project_folder(project_root=".")
                exists = os.path.exists(resolved_folder)
                obs_cfg = provider_manager.resolve_provider_config("obsidian", ".")
                masked = _mask_provider_secrets(obs_cfg)

                project_slug = ""
                map_path = os.path.join(".", ".agents", "knowledge", "obsidian-project-map.json")
                if os.path.exists(map_path):
                    try:
                        with open(map_path, "r", encoding="utf-8") as f:
                            project_slug = json.load(f).get("project_slug", "")
                    except Exception:
                        pass

                res = {
                    "global_config_path": path,
                    "vault_root": obs_cfg.get("vault_root") or obs_cfg.get("vault_path"),
                    "project_slug": project_slug,
                    "resolved_path": resolved_folder,
                    "exists": exists,
                    "sync_mode": obs_cfg.get("mode", "file-sync"),
                    "provider_config": masked
                }
                print(json.dumps(res, indent=2))
            except Exception as e:
                print(json.dumps({"status": "failure", "message": str(e)}, indent=2))
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "sync":
        name = args.name
        if name == "obsidian":
            res = provider_manager.sync_obsidian(project_root=".")
            print(json.dumps(res, indent=2))
        return

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "doctor":
        name = getattr(args, "name", None)
        path = provider_manager.get_global_config_path()
        if name == "obsidian":
            print("Running security and configuration check for Obsidian...")
            if not os.path.exists(path):
                print(f"Global configuration file does not exist at {path}.")
                return
            try:
                resolved = provider_manager.resolve_obsidian_project_folder(project_root=".")
                print(f"[OK] Resolved Obsidian project path: {resolved}")
                if os.path.exists(resolved):
                    print(f"[OK] Resolved path exists.")
                else:
                    print(f"[WARNING] Resolved path does not exist on disk.")

                obs_cfg = provider_manager.resolve_provider_config("obsidian", ".")
                vault_root = obs_cfg.get("vault_root") or obs_cfg.get("vault_path")
                if vault_root:
                    vault_root_abs = os.path.abspath(os.path.expanduser(vault_root))
                    common = os.path.commonpath([vault_root_abs, resolved])
                    if common != vault_root_abs:
                        print(f"[ERROR] Security Violation: Path traversal check failed. Resolved path is outside vault_root.")
                    else:
                        print(f"[OK] Security check passed: Resolved path is inside vault_root.")
                else:
                    print(f"[ERROR] vault_root is not configured.")
            except Exception as e:
                print(f"[ERROR] Obsidian doctor check failed: {e}")
            return

        if not os.path.exists(path):
            print(f"Global configuration file does not exist at {path}.")
            return

        import stat
        try:
            st = os.stat(path)
            mode = st.st_mode
            if os.name != 'nt':
                group_other = mode & (stat.S_IRWXG | stat.S_IRWXO)
                if group_other != 0:
                    print(f"[WARNING] Global config permissions at {path} are too broad: {oct(mode & 0o777)}. Recommended: 600.")
                else:
                    print(f"[OK] Global config permissions at {path} are secure: {oct(mode & 0o777)}.")
            else:
                print(f"[OK] Windows environment detected, file permissions handled by OS.")
        except Exception as e:
            print(f"[ERROR] Failed to read permissions: {e}")
        return

def is_telegram_daemon_running(pid_file: str) -> tuple[bool, int | None]:
    pid = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if os.name == "nt":
                import subprocess
                try:
                    res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    return (str(pid) in res.stdout), pid
                except PermissionError:
                    return False, pid
            os.kill(pid, 0)
            return True, pid
        except Exception:
            return False, pid
    return False, None

def start_telegram_daemon(daemon_script: str, log_file: str, pid_file: str) -> int | None:
    """Start the Telegram daemon, ensuring only ONE instance runs at a time.

    Always kills ALL existing 'workflow_runtime telegram daemon' processes
    (real process scan, not just .pid file) before launching a fresh one.
    This prevents the stale-PID bug where multiple daemons run in parallel
    and Telegram returns 409 Conflict on getUpdates.
    """
    import subprocess
    import time

    # Kill every existing daemon process — real scan, not just .pid file.
    pid_file_pid: int | None = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid_file_pid = int(f.read().strip())
        except Exception:
            pass
    kill_all_telegram_processes(pid_file_pid)

    # Remove stale pid file
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception:
        pass

    # Brief wait so Telegram releases the getUpdates long-poll connection
    time.sleep(1.5)

    os.makedirs(os.path.dirname(pid_file), exist_ok=True)
    log_out = open(log_file, "a", encoding="utf-8")
    cmd = [sys.executable, "-m", "workflow_runtime", "telegram", "daemon"]

    if os.name == "nt":
        proc = subprocess.Popen(
            cmd,
            stdout=log_out,
            stderr=log_out,
            creationflags=0x08000000   # CREATE_NO_WINDOW
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdout=log_out,
            stderr=log_out,
            start_new_session=True
        )

    with open(pid_file, "w", encoding="utf-8") as f:
        f.write(str(proc.pid))
    return proc.pid



__all__ = [
    "_mask_provider_secrets",
    "do_provider_action",
    "ForbiddenAISourceError",
    "extract_work_item_id_from_text",
    "get_current_project_context",
    "is_telegram_daemon_running",
    "sync_analysis_agents_to_session",
]
