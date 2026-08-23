from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def get_global_aiwf_dir() -> Path:
    """Return the global .aiwf directory path in the user's home folder."""
    d = Path.home() / ".aiwf"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_opener(proxy: str | None = None) -> urllib.request.OpenerDirector:
    """Build urllib opener with optional proxy support."""
    opener = urllib.request.build_opener()
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        opener.add_handler(proxy_handler)
    return opener


def load_global_config() -> dict[str, Any]:
    """Load global Telegram configuration from ~/.aiwf/.env.telegram-notify."""
    cfg_path = get_global_aiwf_dir() / ".env.telegram-notify"
    config: dict[str, Any] = {"token": None, "proxy": None}
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "TELEGRAM_BOT_TOKEN":
                            config["token"] = v
                        elif k == "TELEGRAM_PROXY":
                            config["proxy"] = v
        except Exception as e:
            print(f"[WARN] Failed to load global Telegram config: {e}", file=sys.stderr)
    return config


def load_projects_registry() -> dict[str, Any]:
    """Load ~/.aiwf/projects.json registry."""
    reg_path = get_global_aiwf_dir() / "projects.json"
    registry: dict[str, Any] = {"projects": []}
    if reg_path.exists():
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, dict):
                    registry = cast(dict[str, Any], raw_data)
        except Exception as e:
            print(f"[WARN] Failed to load projects registry: {e}", file=sys.stderr)
    return registry


def resolve_project_inbox(project_info: dict[str, Any]) -> tuple[Path, Path] | None:
    """Resolve (project_root, inbox_file) from a registry project entry."""
    path_str = project_info.get("path")
    if not path_str:
        return None
    project_root = Path(str(path_str))
    if not project_root.exists():
        return None
    inbox_file = project_root / ".agents" / "state" / "telegram" / "inbox.json"
    return project_root, inbox_file


def bind_telegram_chat_to_project(project_path: str, chat_id: str) -> bool:
    """Bind a telegram_chat_id to a project entry in ~/.aiwf/projects.json."""
    reg_path = get_global_aiwf_dir() / "projects.json"
    registry = load_projects_registry()

    target_abs = os.path.abspath(project_path)
    updated = False

    raw_projects = registry.get("projects", [])
    projects_list = cast(list[Any], raw_projects) if isinstance(raw_projects, list) else []
    for p_item in projects_list:
        if isinstance(p_item, dict):
            p = cast(dict[str, Any], p_item)
            p_abs = os.path.abspath(str(p.get("path", "")))
            if p_abs == target_abs:
                p["telegram_chat_id"] = str(chat_id)
                updated = True
                break

    if updated:
        try:
            tmp_path = reg_path.with_name("projects.json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, reg_path)
            return True
        except Exception as e:
            print(f"[WARN] Failed to update projects registry: {e}", file=sys.stderr)
    return False


def save_discovered_group(chat_id: str, chat_title: str) -> None:
    """Record group chat info in ~/.aiwf/discovered_groups.json."""
    disc_path = get_global_aiwf_dir() / "discovered_groups.json"
    data: dict[str, Any] = {}
    if disc_path.exists():
        try:
            with open(disc_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = cast(dict[str, Any], loaded)
        except Exception:
            pass

    data[str(chat_id)] = {
        "title": chat_title,
        "last_seen": datetime.now(timezone.utc).isoformat()
    }

    try:
        tmp_path = disc_path.with_name("discovered_groups.json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, disc_path)
    except Exception as e:
        print(f"[WARN] Failed to save discovered group: {e}", file=sys.stderr)


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for project inbox events."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_inbox_payload(event_type: str, content: str, update_id: Any, chat_id: str) -> dict[str, Any]:
    """Build the canonical project-local Telegram inbox JSON object."""
    return {
        "type": event_type,
        "content": content,
        "update_id": update_id,
        "chat_id": chat_id,
        "timestamp": utc_timestamp(),
    }


def build_outbox_payload(content: str, chat_id: str, reply_to_update_id: Any = None) -> dict[str, Any]:
    """Build the canonical project-local Telegram outbox JSON object."""
    payload: dict[str, Any] = {
        "type": "TELEGRAM_REPLY",
        "content": content,
        "chat_id": str(chat_id),
        "timestamp": utc_timestamp(),
    }
    if reply_to_update_id is not None:
        payload["reply_to_update_id"] = reply_to_update_id
    return payload


def write_inbox_payload_atomic(inbox_file: Path, payload: dict[str, Any]) -> None:
    """Write inbox JSON atomically via inbox.json.tmp followed by os.replace.
    Appends to existing array to prevent message loss.
    """
    inbox_file.parent.mkdir(parents=True, exist_ok=True)

    queue: list[dict[str, Any]] = []
    if inbox_file.exists():
        try:
            with open(inbox_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    queue = cast(list[dict[str, Any]], data)
                elif isinstance(data, dict):
                    queue = [cast(dict[str, Any], data)]
        except Exception:
            pass

    queue.append(payload)

    tmp_inbox = inbox_file.with_name("inbox.json.tmp")
    with open(tmp_inbox, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")

    os.replace(tmp_inbox, inbox_file)


def project_relative_path(project_root: Path, abs_target: Path) -> str:
    """Return relative path string if inside project_root, else absolute string."""
    try:
        rel = abs_target.relative_to(project_root)
        return str(rel).replace("\\", "/")
    except ValueError:
        return str(abs_target).replace("\\", "/")


__all__ = [
    "get_global_aiwf_dir",
    "get_opener",
    "load_global_config",
    "load_projects_registry",
    "resolve_project_inbox",
    "bind_telegram_chat_to_project",
    "save_discovered_group",
    "utc_timestamp",
    "build_inbox_payload",
    "build_outbox_payload",
    "write_inbox_payload_atomic",
    "project_relative_path",
]
