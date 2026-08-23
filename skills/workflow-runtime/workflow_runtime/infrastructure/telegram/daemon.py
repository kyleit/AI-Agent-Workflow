from __future__ import annotations

from typing import Any, cast

# skills/workflow-runtime/workflow_runtime/infrastructure/telegram/daemon.py
"""Telegram daemon core: polling loop, message router, and TelegramDaemonManager.

Imports helpers from:
- daemon_utils    : config, registry, inbox/outbox IO, path helpers
- outbox_sender   : all outbound send functions + multi-type dispatcher
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        getattr(sys.stderr, "reconfigure")(encoding="utf-8")
except Exception:
    pass

if sys.platform == "win32":
    py_dir = os.path.dirname(sys.executable)
    if py_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = py_dir + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(py_dir)
    except Exception:
        pass

# ── Imports from split modules ─────────────────────────────────────────────────
from .daemon_utils import (bind_telegram_chat_to_project, build_inbox_payload,
                           get_global_aiwf_dir, load_global_config,
                           load_projects_registry, project_relative_path,
                           resolve_project_inbox, save_discovered_group,
                           write_inbox_payload_atomic)
from .outbox_sender import (process_project_outboxes, send_telegram_ack,
                            send_telegram_buttons, send_telegram_commands,
                            send_telegram_document, send_telegram_photo,
                            send_telegram_url)

# ── Network opener ─────────────────────────────────────────────────────────────

def get_opener(proxy: str | None = None):
    """Build urllib opener with optional proxy support."""
    opener = urllib.request.build_opener()
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        opener.add_handler(proxy_handler)
    return opener


# ── Telegram API helpers ──────────────────────────────────────────────────────

def send_telegram_reaction(
    token: str, chat_id: str, message_id: int, emoji: str, proxy: str | None = None
) -> None:
    """Add reaction to a message on Telegram."""
    url = f"https://api.telegram.org/bot{token}/setMessageReaction"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": json.dumps([{"type": "emoji", "emoji": emoji}])
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp.read()
    except Exception as e:
        print(f"[WARN] Failed to send Telegram reaction: {e}", file=sys.stderr)


def download_telegram_file(
    token: str, file_id: str, dest_path: Path, proxy: str | None = None
) -> bool:
    """Download a file from Telegram servers using file_id."""
    url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    try:
        with get_opener(proxy).open(url, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if not res.get("ok"):
                return False
            file_path = res["result"].get("file_path")
            if not file_path:
                return False
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with get_opener(proxy).open(download_url, timeout=30) as incoming:
            with open(dest_path, "wb") as out:
                out.write(incoming.read())
        return True
    except Exception as e:
        print(f"[WARN] Failed to download media file: {e}", file=sys.stderr)
        return False


# ── Message router ─────────────────────────────────────────────────────────────

def route_update(token: str, update: dict[str, Any], proxy: str | None = None) -> None:
    """Route a single incoming Telegram update to the corresponding project inbox."""
    msg_raw = update.get("message")
    if not isinstance(msg_raw, dict):
        return
    msg = cast(dict[str, Any], msg_raw)

    chat: dict[str, Any] = cast(dict[str, Any], msg.get("chat", {})) if isinstance(msg.get("chat"), dict) else {}
    chat_id = str(chat.get("id", ""))
    chat_title = str(chat.get("title") or chat.get("username") or chat.get("first_name") or "Unknown Chat")
    print(
        f"[DAEMON] Received update_id={update.get('update_id')} from chat_id={chat_id} "
        f"({chat_title}): {msg.get('text', msg.get('caption', '[media]'))}",
        flush=True,
    )
    chat_type = str(chat.get("type", ""))

    if chat_type in ["group", "supergroup"]:
        save_discovered_group(chat_id, chat_title)

    text = str(msg.get("text", ""))
    photo: list[dict[str, Any]] | None = cast(list[dict[str, Any]], msg.get("photo")) if isinstance(msg.get("photo"), list) else None
    document: dict[str, Any] | None = cast(dict[str, Any], msg.get("document")) if isinstance(msg.get("document"), dict) else None
    update_id = str(update.get("update_id", "0"))

    # 1. Match by Chat/Group ID (direct routing)
    registry = load_projects_registry()
    target_project: dict[str, Any] | None = None
    clean_msg = ""

    for p in registry.get("projects", []):
        if p.get("telegram_chat_id") == chat_id:
            target_project = p
            break

    # 2. Fallback: match by slash command /<project_name>
    if not target_project and text:
        text_lower = text.lower().strip()
        for p in registry.get("projects", []):
            name = p["name"].lower()
            name_underscores = name.replace("-", "_")
            if text_lower.startswith(f"/{name}"):
                target_project = p
                clean_msg = text[len(f"/{name}"):].strip()
                break
            elif text_lower.startswith(f"/{name_underscores}"):
                target_project = p
                clean_msg = text[len(f"/{name_underscores}"):].strip()
                break

    # 3. Fallback: private message → first active project
    if not target_project and chat_type == "private":
        active = [p for p in registry.get("projects", []) if p.get("status") == "active"]
        if active:
            target_project = active[0]
            clean_msg = text

    # 4. Fallback: group → first active project, auto-bind
    if not target_project and chat_type in ["group", "supergroup"]:
        active = [p for p in registry.get("projects", []) if p.get("status") == "active"]
        if active:
            target_project = active[0]
            clean_msg = text
            if target_project and "path" in target_project:
                try:
                    bind_telegram_chat_to_project(str(target_project["path"]), chat_id)
                except Exception:
                    pass

    if not target_project:
        return

    # Acknowledge receipt with 👀 reaction
    message_id = cast(int, msg.get("message_id", 0))
    if message_id:
        send_telegram_reaction(token, chat_id, message_id, "👀", proxy)

    inbox_target = resolve_project_inbox(target_project)
    if not inbox_target:
        print(
            f"[WARN] Registered project path is unavailable; cannot write Telegram inbox "
            f"for {target_project.get('name')}",
            file=sys.stderr,
        )
        return
    project_root, inbox_file = inbox_target
    inbox_file.parent.mkdir(parents=True, exist_ok=True)

    inbox_payload = None
    if photo:
        largest = photo[-1]
        file_id = str(largest.get("file_id", ""))
        photo_path = inbox_file.parent / "photos" / f"{update_id}.jpg"
        if download_telegram_file(token, file_id, photo_path, proxy):
            inbox_payload = build_inbox_payload(
                "PHOTO_RECEIVED", project_relative_path(project_root, photo_path), update_id, chat_id
            )
        else:
            inbox_payload = build_inbox_payload("PHOTO_DOWNLOAD_FAILED", file_id, update_id, chat_id)
    elif document:
        file_id = str(document.get("file_id", ""))
        orig_name = str(document.get("file_name", f"file_{update_id}"))
        file_path = inbox_file.parent / "files" / f"{update_id}_{orig_name}"
        if download_telegram_file(token, file_id, file_path, proxy):
            inbox_payload = build_inbox_payload(
                "FILE_RECEIVED", project_relative_path(project_root, file_path), update_id, chat_id
            )
        else:
            inbox_payload = build_inbox_payload("FILE_DOWNLOAD_FAILED", file_id, update_id, chat_id)
    else:
        msg_content = clean_msg if clean_msg else text
        inbox_payload = build_inbox_payload("MESSAGE_RECEIVED", msg_content, update_id, chat_id)

    if inbox_payload:
        try:
            write_inbox_payload_atomic(inbox_file, inbox_payload)
        except Exception as e:
            print(f"[WARN] Failed to write project inbox: {e}", file=sys.stderr)


# ── Bot menu commands ──────────────────────────────────────────────────────────

def set_bot_menu_commands(token: str, proxy: str | None = None) -> None:
    """Sync registered project commands to Telegram API (setMyCommands)."""
    registry = load_projects_registry()
    commands: list[dict[str, str]] = []
    seen: set[str] = set()

    current_name = os.path.basename(os.path.abspath(".")).lower()
    projects: list[Any] = cast(list[Any], registry.get("projects", [])) if isinstance(registry.get("projects"), list) else []
    active_projects = [p for p in projects if p.get("status") == "active"]
    active_projects.sort(key=lambda p: p.get("name", "").lower() != current_name)
    other_projects = [p for p in projects if p.get("status") != "active"]

    for p in active_projects + other_projects:
        if len(commands) >= 95:
            break
        name = p["name"].lower()
        cmd_name = re.sub(r"[^a-z0-9_]", "_", name.replace("-", "_"))
        cmd_name = re.sub(r"_+", "_", cmd_name)[:32].strip("_")
        if cmd_name and re.match(r"^[a-z][a-z0-9_]*$", cmd_name) and len(cmd_name) <= 32:
            if "tmp" in cmd_name or cmd_name in seen:
                continue
            seen.add(cmd_name)
            commands.append({"command": cmd_name, "description": f"Gui lenh cho du an {p['name']}"})

    if not commands:
        return

    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    data = json.dumps({"commands": commands}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp.read()
    except Exception as e:
        print(f"[WARN] Failed to register Telegram bot commands: {e}", file=sys.stderr)


# ── Polling loop ───────────────────────────────────────────────────────────────

def run_polling_loop(supervised: bool = False) -> None:
    """Main daemon execution loop (long-polling getUpdates)."""
    if not supervised:
        import socket
        try:
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            lock_socket.bind(("127.0.0.1", 27124))
        except OSError:
            print("Telegram daemon is already running in another process.", file=sys.stderr)
            sys.exit(1)

    print("Initializing Telegram Shared Daemon...", flush=True)
    config = load_global_config()
    token = config["token"]
    proxy = config["proxy"]

    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in ~/.aiwf/.env.telegram-notify", file=sys.stderr)
        if supervised:
            return
        sys.exit(1)

    offset_file = get_global_aiwf_dir() / "telegram-offset.txt"
    offset = 0
    if offset_file.exists():
        try:
            with open(offset_file, "r", encoding="utf-8") as f:
                offset = int(f.read().strip())
        except Exception:
            pass

    print(f"Polling loop started using offset: {offset}", flush=True)

    while True:
        try:
            config = load_global_config()
            token = config["token"]
            proxy = config["proxy"]
            if not token:
                time.sleep(5)
                continue

            process_project_outboxes(token, proxy)

            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=25"
            with get_opener(proxy).open(urllib.request.Request(url, method="GET"), timeout=35) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if not res.get("ok"):
                    time.sleep(5)
                    continue
                for u in res.get("result", []):
                    route_update(token, u, proxy)
                    offset = max(offset, u["update_id"] + 1)
                    with open(offset_file, "w", encoding="utf-8") as f:
                        f.write(str(offset))

            process_project_outboxes(token, proxy)

        except Exception as ex:
            print(f"[WARN] Long polling exception encountered: {ex}", file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        run_polling_loop()
    else:
        print("Usage: python telegram_daemon.py daemon")
        sys.exit(1)


# ── TelegramDaemonManager ──────────────────────────────────────────────────────

class TelegramDaemonManager:
    """Manages the shared Telegram daemon lifecycle.

    Supported outbox.json types:
    1. TELEGRAM_REPLY          – text message
    2. TELEGRAM_SEND_DOCUMENT  – file upload (sendDocument)
    3. TELEGRAM_SEND_PHOTO     – image upload (sendPhoto)
    4. TELEGRAM_SEND_URL       – URL with link preview
    5. TELEGRAM_SEND_BUTTONS   – inline keyboard (InlineKeyboardMarkup)
    6. TELEGRAM_SEND_COMMANDS  – set bot menu commands (setMyCommands)
    7. TELEGRAM_SEND_REACTION  – emoji reaction (setMessageReaction)
    """

    def __init__(self) -> None:
        pass

    # ── Send wrappers ─────────────────────────────────────────────────────
    def send_message(self, token: str, chat_id: str, text: str,
                     proxy: str | None = None) -> bool:
        return send_telegram_ack(token, chat_id, text, proxy)

    def send_document(self, token: str, chat_id: str, file_path: str,
                      caption: str = "", proxy: str | None = None) -> bool:
        return send_telegram_document(token, chat_id, file_path, caption, proxy)

    def send_photo(self, token: str, chat_id: str, file_path: str,
                   caption: str = "", proxy: str | None = None) -> bool:
        return send_telegram_photo(token, chat_id, file_path, caption, proxy)

    def send_url(self, token: str, chat_id: str, url: str,
                 caption: str = "", proxy: str | None = None) -> bool:
        return send_telegram_url(token, chat_id, url, caption, proxy)

    def send_buttons(self, token: str, chat_id: str, text: str,
                     buttons: list[list[dict[str, Any]]], proxy: str | None = None) -> bool:
        return send_telegram_buttons(token, chat_id, text, cast(list[Any], buttons), proxy)

    def send_commands(self, token: str, commands: list[dict[str, Any]],
                      scope: dict[str, Any] | None = None, language_code: str = "",
                      proxy: str | None = None) -> bool:
        return send_telegram_commands(token, commands, scope, language_code, proxy)

    def send_reaction(self, token: str, chat_id: str, message_id: int,
                      emoji: str = "👍", proxy: str | None = None) -> None:
        return send_telegram_reaction(token, chat_id, message_id, emoji, proxy)

    def process_outboxes(self, token: str, proxy: str | None = None) -> None:
        return process_project_outboxes(token, proxy)

    # ── Registry helpers ──────────────────────────────────────────────────
    def load_projects_registry(self) -> dict[str, Any]:
        return load_projects_registry()

    def load_telegram_config(self) -> dict[str, Any]:
        return load_global_config()

    # ── Daemon script path ────────────────────────────────────────────────
    @property
    def daemon_script(self) -> Path:
        return Path(__file__).resolve()

    def start_process(self, daemon_mode: bool = True) -> subprocess.Popen[Any] | None:
        """Launch the daemon as a background subprocess."""
        if not Path(__file__).resolve().exists():
            return None
        cmd = [sys.executable, str(Path(__file__).resolve())]
        if daemon_mode:
            cmd.append("daemon")
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Module-level convenience instance
daemon = TelegramDaemonManager()
