# skills/workflow-runtime/scripts/telegram_daemon.py
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import re
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
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


def get_global_aiwf_dir() -> Path:
    """Return the global .aiwf directory path in the user's home folder."""
    d = Path.home() / ".aiwf"
    d.mkdir(parents=True, exist_ok=True)
    return d

def load_global_config() -> dict:
    """Load global Telegram configuration from ~/.aiwf/.env.telegram-notify."""
    cfg_path = get_global_aiwf_dir() / ".env.telegram-notify"
    config = {"token": None, "proxy": None}
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
            print(f"[WARN] Failed to parse global config: {e}", file=sys.stderr)
    return config

def get_registry_dir() -> Path:
    """Determine OS-specific configuration directory for registry."""
    import platform
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "aiwf"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "aiwf"
    
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "aiwf"
    return Path.home() / ".config" / "aiwf"

def load_projects_registry() -> dict:
    """Load global registered projects from projects.json."""
    reg_path = get_registry_dir() / "projects.json"
    if reg_path.exists():
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"projects": []}

def resolve_project_inbox(target_project: dict) -> tuple[Path, Path] | None:
    """Return (project_root, inbox_file) for a registered project-local inbox."""
    project_path = target_project.get("path")
    if not project_path:
        return None
    try:
        project_root = Path(project_path).expanduser().resolve()
    except Exception:
        return None
    if not project_root.exists() or not project_root.is_dir():
        return None
    inbox_dir = project_root / ".agents" / "inbox"
    inbox_file = inbox_dir / "inbox.json"
    try:
        resolved_inbox = inbox_file.resolve()
        if not str(resolved_inbox).startswith(str(project_root)):
            return None
    except Exception:
        return None
    return project_root, inbox_file

def project_relative_path(project_root: Path, path: Path) -> str:
    """Format paths in inbox payloads relative to the registered project root."""
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except Exception:
        return path.as_posix()

def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for project inbox events."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def build_inbox_payload(event_type: str, content: str, update_id, chat_id: str) -> dict:
    """Build the canonical project-local Telegram inbox JSON object."""
    return {
        "type": event_type,
        "content": content,
        "update_id": update_id,
        "chat_id": chat_id,
        "timestamp": utc_timestamp(),
    }

def build_outbox_payload(content: str, chat_id: str, reply_to_update_id=None) -> dict:
    """Build the canonical project-local Telegram outbox JSON object."""
    payload = {
        "type": "TELEGRAM_REPLY",
        "content": content,
        "chat_id": str(chat_id),
        "timestamp": utc_timestamp(),
    }
    if reply_to_update_id is not None:
        payload["reply_to_update_id"] = reply_to_update_id
    return payload

def write_inbox_payload_atomic(inbox_file: Path, payload: dict) -> None:
    """Write inbox JSON atomically via inbox.json.tmp followed by os.replace."""
    inbox_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_inbox = inbox_file.with_name("inbox.json.tmp")
    with open(tmp_inbox, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_inbox, inbox_file)

def write_outbox_payload_atomic(outbox_file: Path, payload: dict) -> None:
    """Write outbox JSON atomically via outbox.json.tmp followed by os.replace."""
    outbox_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_outbox = outbox_file.with_name("outbox.json.tmp")
    with open(tmp_outbox, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_outbox, outbox_file)

def save_discovered_group(chat_id: str, chat_title: str) -> None:
    """Save unique group details dynamically to ~/.aiwf/discovered_groups.json."""
    disc_path = get_global_aiwf_dir() / "discovered_groups.json"
    data = {}
    if disc_path.exists():
        try:
            with open(disc_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    
    data[str(chat_id)] = chat_title
    
    try:
        tmp_path = disc_path.with_name("discovered_groups.json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, disc_path)
    except Exception as e:
        print(f"[WARN] Failed to save discovered group: {e}", file=sys.stderr)

def bind_telegram_chat_to_project(project_path: str, chat_id: str) -> None:
    """Auto-bind telegram_chat_id to project in projects.json."""
    reg_path = get_registry_dir() / "projects.json"
    if not reg_path.exists():
        return
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        modified = False
        norm_target = str(Path(project_path).resolve())
        for p in data.get("projects", []):
            try:
                p_norm = str(Path(p.get("path", "")).resolve())
                if p_norm == norm_target:
                    if p.get("telegram_chat_id") != str(chat_id):
                        p["telegram_chat_id"] = str(chat_id)
                        modified = True
            except Exception:
                pass
        if modified:
            tmp_path = reg_path.with_name("projects.json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, reg_path)
    except Exception as e:
        print(f"[WARN] Failed to auto-bind Telegram chat_id to project: {e}", file=sys.stderr)

def get_opener(proxy: str = None):
    """Build urllib opener with optional proxy support."""
    opener = urllib.request.build_opener()
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy,
            "https": proxy
        })
        opener.add_handler(proxy_handler)
    return opener

def send_telegram_ack(token: str, chat_id: str, text: str, proxy: str = None) -> bool:
    """Send immediate acknowledgement/reply message back to Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp.read()
        return True
    except Exception as e:
        print(f"[WARN] Failed to send Telegram ack: {e}", file=sys.stderr)
        return False

def validate_outbox_payload(payload: dict) -> tuple[str, str]:
    """Return (chat_id, content) after validating the outbox payload."""
    if not isinstance(payload, dict):
        raise ValueError("Telegram outbox payload must be a JSON object")
    if payload.get("type") != "TELEGRAM_REPLY":
        raise ValueError(f"Unsupported Telegram outbox type: {payload.get('type')}")
    chat_id = str(payload.get("chat_id", "")).strip()
    content = str(payload.get("content", "")).strip()
    if not chat_id:
        raise ValueError("Telegram outbox payload is missing chat_id")
    if not content:
        raise ValueError("Telegram outbox payload is missing content")
    return chat_id, content

def process_project_outboxes(token: str, proxy: str = None) -> None:
    """Send queued project-local Telegram replies without requiring the agent to run commands."""
    registry = load_projects_registry()
    for project in registry.get("projects", []):
        inbox_target = resolve_project_inbox(project)
        if not inbox_target:
            continue
        _, inbox_file = inbox_target
        outbox_file = inbox_file.with_name("outbox.json")
        if not outbox_file.exists():
            continue
        try:
            with open(outbox_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            chat_id, content = validate_outbox_payload(payload)
            if not send_telegram_ack(token, chat_id, content, proxy):
                continue
            sent_file = outbox_file.with_name("outbox.sent.json")
            tmp_sent = outbox_file.with_name("outbox.sent.json.tmp")
            with open(tmp_sent, "w", encoding="utf-8") as f:
                json.dump({**payload, "sent_at": utc_timestamp()}, f, indent=2, ensure_ascii=False)
                f.write("\n")
            os.replace(tmp_sent, sent_file)
            os.remove(outbox_file)
        except Exception as e:
            print(f"[WARN] Failed to process Telegram outbox for {project.get('name')}: {e}", file=sys.stderr)

def send_telegram_reaction(token: str, chat_id: str, message_id: int, emoji: str, proxy: str = None) -> None:
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


def download_telegram_file(token: str, file_id: str, dest_path: Path, proxy: str = None) -> bool:
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

def route_update(token: str, update: dict, proxy: str = None) -> None:
    """Route a single update message to the corresponding project inbox."""
    msg = update.get("message")
    if not msg:
        return
        
    chat = msg.get("chat", {})
    chat_id = str(chat.get("id", ""))
    chat_title = chat.get("title") or chat.get("username") or chat.get("first_name") or "Unknown Chat"
    print(f"[DAEMON] Received update_id={update.get('update_id')} from chat_id={chat_id} ({chat_title}): {msg.get('text', msg.get('caption', '[media]'))}", flush=True)
    chat_type = msg.get("chat", {}).get("type", "")
    
    # Store group details if it's a group/supergroup
    if chat_type in ["group", "supergroup"]:
        save_discovered_group(chat_id, chat_title)
        
    text = msg.get("text", "")
    caption = msg.get("caption", "")
    photo = msg.get("photo")
    document = msg.get("document")
    update_id = update.get("update_id")
    
    # Find matching project from registry
    registry = load_projects_registry()
    target_project = None
    clean_msg = ""
    
    # 1. Match by Chat/Group ID first (Direct Routing)
    for p in registry.get("projects", []):
        if p.get("telegram_chat_id") == chat_id:
            target_project = p
            break
            
    # 2. Fallback: match by slash command prefix /<project_name> or /<project_name_underscores>
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
                
    # 3. Fallback: if it's direct message to bot, route to the first active/default project
    if not target_project and chat_type == "private":
        active_projects = [p for p in registry.get("projects", []) if p.get("status") == "active"]
        if active_projects:
            target_project = active_projects[0]
            clean_msg = text

    # 4. Fallback for group/supergroup: route to active project if unmapped
    if not target_project and chat_type in ["group", "supergroup"]:
        active_projects = [p for p in registry.get("projects", []) if p.get("status") == "active"]
        if active_projects:
            target_project = active_projects[0]
            clean_msg = text
            try:
                bind_telegram_chat_to_project(target_project["path"], chat_id)
            except Exception:
                pass
            
    if not target_project:
        # No project mapped, ignore
        return
        
    # React with 👀 emoji to acknowledge receipt silently
    message_id = msg.get("message_id")
    if message_id:
        send_telegram_reaction(token, chat_id, message_id, "👀", proxy)

    inbox_target = resolve_project_inbox(target_project)
    if not inbox_target:
        print(f"[WARN] Registered project path is unavailable; cannot write Telegram inbox for {target_project.get('name')}", file=sys.stderr)
        return
    project_root, inbox_file = inbox_target
    project_inbox_dir = inbox_file.parent
    project_inbox_dir.mkdir(parents=True, exist_ok=True)
        
    # Write payload based on message type
    inbox_payload = None
    
    if photo:
        # Choose the largest photo size
        largest = photo[-1]
        file_id = largest["file_id"]
        filename = f"{update_id}.jpg"
        photo_dir = project_inbox_dir / "photos"
        photo_path = photo_dir / filename
        
        # Immediate Telegram ack (disabled to avoid spam, see 2026-07-19 rules)
        # send_telegram_ack(token, chat_id, f"✅ [{target_project['name']}] Đang tải ảnh...", proxy)
        
        if download_telegram_file(token, file_id, photo_path, proxy):
            inbox_payload = build_inbox_payload(
                "PHOTO_RECEIVED",
                project_relative_path(project_root, photo_path),
                update_id,
                chat_id,
            )
        else:
            inbox_payload = build_inbox_payload("PHOTO_DOWNLOAD_FAILED", file_id, update_id, chat_id)
            
    elif document:
        file_id = document["file_id"]
        orig_name = document.get("file_name", f"file_{update_id}")
        file_dir = project_inbox_dir / "files"
        file_path = file_dir / f"{update_id}_{orig_name}"
        
        # send_telegram_ack(token, chat_id, f"✅ [{target_project['name']}] Đang tải tệp tin...", proxy)
        
        if download_telegram_file(token, file_id, file_path, proxy):
            inbox_payload = build_inbox_payload(
                "FILE_RECEIVED",
                project_relative_path(project_root, file_path),
                update_id,
                chat_id,
            )
        else:
            inbox_payload = build_inbox_payload("FILE_DOWNLOAD_FAILED", file_id, update_id, chat_id)
            
    else:
        # Standard text message
        msg_content = clean_msg if clean_msg else text
        inbox_payload = build_inbox_payload("MESSAGE_RECEIVED", msg_content, update_id, chat_id)
        
    # Write inbox payload atomically
    if inbox_payload:
        try:
            write_inbox_payload_atomic(inbox_file, inbox_payload)
            
            # Send success ack (disabled to avoid spam)
            # send_telegram_ack(token, chat_id, f"✅ [{target_project['name']}] Đã nhận, đang chuyển tiếp cho Agent...", proxy)
        except Exception as e:
            print(f"[WARN] Failed to write project inbox: {e}", file=sys.stderr)

def set_bot_menu_commands(token: str, proxy: str = None) -> None:
    """Sync registered project commands to Telegram API."""
    registry = load_projects_registry()
    commands = []
    seen = set()
    
    current_name = os.path.basename(os.path.abspath(".")).lower()
    projects = registry.get("projects", [])
    active_projects = [p for p in projects if p.get("status") == "active"]
    active_projects.sort(key=lambda p: p.get("name", "").lower() != current_name)
    other_projects = [p for p in projects if p.get("status") != "active"]
    
    for p in active_projects + other_projects:
        if len(commands) >= 95:
            break
        name = p["name"].lower()
        cmd_name = re.sub(r"[^a-z0-9_]", "_", name.replace("-", "_"))
        cmd_name = re.sub(r"_+", "_", cmd_name)[:32].strip("_")
        # Strict Telegram command validation: must start with letter, lowercase, no consecutive underscores
        if cmd_name and re.match(r"^[a-z][a-z0-9_]*$", cmd_name) and len(cmd_name) <= 32:
            # Filter out temporary test directory names
            if "tmp" in cmd_name:
                continue
            if cmd_name not in seen:
                seen.add(cmd_name)
                commands.append({
                    "command": cmd_name,
                    "description": f"Gui lenh cho du an {p['name']}"
                })
            
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

def run_polling_loop() -> None:
    """Main daemon execution loop."""
    print("Initializing Telegram Shared Daemon...", flush=True)
    config = load_global_config()
    token = config["token"]
    proxy = config["proxy"]
    
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in ~/.aiwf/.env.telegram-notify", file=sys.stderr)
        sys.exit(1)
        
    # Sync dynamic commands
    # set_bot_menu_commands(token, proxy)
    
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
            # Check for config reload dynamically (allows hot-swapping tokens)
            config = load_global_config()
            token = config["token"]
            proxy = config["proxy"]
            if not token:
                time.sleep(5)
                continue

            process_project_outboxes(token, proxy)
                
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=25"
            req = urllib.request.Request(url, method="GET")
            
            with get_opener(proxy).open(req, timeout=35) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if not res.get("ok"):
                    time.sleep(5)
                    continue
                    
                updates = res.get("result", [])
                for u in updates:
                    route_update(token, u, proxy)
                    offset = max(offset, u["update_id"] + 1)
                    with open(offset_file, "w", encoding="utf-8") as f:
                        f.write(str(offset))

            process_project_outboxes(token, proxy)
                        
        except Exception as ex:
            # Handle net timeouts, network dropouts gracefully without exiting
            print(f"[WARN] Long polling exception encountered: {ex}", file=sys.stderr)
            time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        run_polling_loop()
    else:
        print("Usage: python telegram_daemon.py daemon")
        sys.exit(1)
