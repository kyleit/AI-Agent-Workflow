"""
workflow_runtime/presentation/cli/telegram_notifier.py

Telegram startup notification sender for AIWF CLI.
"""
from __future__ import annotations

import os
import sys
from typing import Any


def send_telegram_startup_message(conversation_id: str) -> None:
    env_path = os.path.join(".agents", "config", ".env.telegram-notify")
    if not os.path.exists(env_path):
        return

    token = None
    chat_id = None
    proxy = None
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "TELEGRAM_BOT_TOKEN":
                        token = v
                    elif k == "TELEGRAM_CHAT_ID":
                        chat_id = v
                    elif k == "TELEGRAM_PROXY":
                        proxy = v
    except Exception as e:
        print(f"Warning: Failed to parse .env.telegram-notify: {e}", file=sys.stderr)
        return

    if not token or not chat_id:
        return

    # Try to resolve project-specific chat_id from projects.json registry
    try:
        import json
        import platform
        from pathlib import Path

        system = platform.system()
        reg_dir = Path.home() / ".config" / "aiwf"
        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                reg_dir = Path(appdata) / "aiwf"
        elif system == "Darwin":
            reg_dir = Path.home() / "Library" / "Application Support" / "aiwf"

        reg_path = reg_dir / "projects.json"
        if reg_path.exists():
            with open(reg_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            curr_abs = str(Path(".").resolve()).lower()
            for p in registry.get("projects", []):
                if str(Path(p["path"]).resolve()).lower() == curr_abs:
                    if p.get("telegram_chat_id"):
                        chat_id = p["telegram_chat_id"]
                        break
    except Exception:
        json: Any = None
    project_name = "default"
    manifest_path = "MANIFEST.json"
    if os.path.exists(manifest_path):
        try:
            import json as _json

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = _json.load(f)
                project_name = manifest_data.get("name", "default")
        except Exception:
            pass

    message = f"\U0001f916 [{project_name}] Khởi động thành công và sẵn sàng nhận lệnh.\nConversation ID: {conversation_id}"

    import urllib.parse
    import urllib.request

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    opener = urllib.request.build_opener()
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        opener.add_handler(proxy_handler)

    try:
        with opener.open(req, timeout=15) as response:
            response.read()
    except Exception as e:
        print(
            f"Warning: Failed to send Telegram startup notification: {e}",
            file=sys.stderr,
        )
