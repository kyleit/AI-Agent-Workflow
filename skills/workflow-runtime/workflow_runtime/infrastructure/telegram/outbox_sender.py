from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, cast

from .daemon_utils import (get_opener, load_projects_registry,
                           resolve_project_inbox, utc_timestamp)

# ── Supported outbox types ─────────────────────────────────────────────────────

_SUPPORTED_OUTBOX_TYPES = {
    "TELEGRAM_REPLY",
    "TELEGRAM_SEND_DOCUMENT",
    "TELEGRAM_SEND_PHOTO",
    "TELEGRAM_SEND_URL",
    "TELEGRAM_SEND_BUTTONS",
    "TELEGRAM_SEND_COMMANDS",
}


# ── Low-level network helpers ─────────────────────────────────────────────────

def send_telegram_ack(token: str, chat_id: str, text: str, proxy: str | None = None) -> bool:
    """Send a plain-text reply via Telegram sendMessage API."""
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp_data = resp.read()
            res_str = resp_data.decode("utf-8") if isinstance(resp_data, bytes) else str(resp_data)
            result = cast(dict[str, Any], json.loads(res_str))
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"[WARN] Failed to send Telegram ack: {e}", file=sys.stderr)
        return False


def _build_multipart_body_multi(
    fields: dict[str, Any], files: dict[str, tuple[Path, str]]
) -> tuple[bytes, str]:
    """Build a RFC2388 multipart/form-data body for Telegram file uploads."""
    import uuid
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for key, val in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode("utf-8")
        )
    for file_field, (file_path, mime_type) in files.items():
        filename = file_path.name
        file_header = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
        parts.append(file_header + file_path.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


# ── Send functions ─────────────────────────────────────────────────────────────

def send_telegram_document(
    token: str, chat_id: str, file_path: str | list[str], caption: str = "", proxy: str | None = None
) -> bool:
    """Send a file or multiple files as Telegram documents."""
    file_paths: list[str] = [file_path] if isinstance(file_path, str) else list(file_path)
    paths: list[Path] = []
    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            print(f"[WARN] Document file not found: {fp}", file=sys.stderr)
            return False
        paths.append(p)

    if len(paths) == 1:
        api_url = f"https://api.telegram.org/bot{token}/sendDocument"
        fields: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            fields["caption"] = caption
        files = {"document": (paths[0], "application/octet-stream")}
    else:
        api_url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
        fields = {"chat_id": chat_id}
        media: list[dict[str, str]] = []
        files: dict[str, tuple[Path, str]] = {}
        for i, p in enumerate(paths):
            attach_name = f"doc{i}"
            files[attach_name] = (p, "application/octet-stream")
            media_item: dict[str, str] = {"type": "document", "media": f"attach://{attach_name}"}
            if i == 0 and caption:
                media_item["caption"] = caption
            media.append(media_item)
        fields["media"] = json.dumps(media)

    try:
        body, content_type = _build_multipart_body_multi(fields, files)
        req = urllib.request.Request(api_url, data=body, method="POST")
        req.add_header("Content-Type", content_type)
        with get_opener(proxy).open(req, timeout=30) as resp:
            resp_data = resp.read()
            res_str = resp_data.decode("utf-8") if isinstance(resp_data, bytes) else str(resp_data)
            result = cast(dict[str, Any], json.loads(res_str))
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"[WARN] Failed to send Telegram document: {e}", file=sys.stderr)
        return False


def send_telegram_photo(
    token: str, chat_id: str, photo_path: str | list[str], caption: str = "", proxy: str | None = None
) -> bool:
    """Send a photo or multiple photos via Telegram sendPhoto/sendMediaGroup API."""
    photo_paths: list[str] = [photo_path] if isinstance(photo_path, str) else list(photo_path)
    paths: list[Path] = []
    for fp in photo_paths:
        p = Path(fp)
        if not p.exists():
            print(f"[WARN] Photo file not found: {fp}", file=sys.stderr)
            return False
        paths.append(p)

    if len(paths) == 1:
        api_url = f"https://api.telegram.org/bot{token}/sendPhoto"
        fields: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            fields["caption"] = caption
        files = {"photo": (paths[0], "image/jpeg")}
    else:
        api_url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
        fields = {"chat_id": chat_id}
        media: list[dict[str, str]] = []
        files: dict[str, tuple[Path, str]] = {}
        for i, p in enumerate(paths):
            attach_name = f"photo{i}"
            files[attach_name] = (p, "image/jpeg")
            media_item: dict[str, str] = {"type": "photo", "media": f"attach://{attach_name}"}
            if i == 0 and caption:
                media_item["caption"] = caption
            media.append(media_item)
        fields["media"] = json.dumps(media)

    try:
        body, content_type = _build_multipart_body_multi(fields, files)
        req = urllib.request.Request(api_url, data=body, method="POST")
        req.add_header("Content-Type", content_type)
        with get_opener(proxy).open(req, timeout=30) as resp:
            resp_data = resp.read()
            res_str = resp_data.decode("utf-8") if isinstance(resp_data, bytes) else str(resp_data)
            result = cast(dict[str, Any], json.loads(res_str))
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"[WARN] Failed to send Telegram photo: {e}", file=sys.stderr)
        return False


def send_telegram_url(token: str, chat_id: str, url: str, caption: str = "", proxy: str | None = None) -> bool:
    """Send a web URL (link preview) via Telegram sendMessage API."""
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = f"{caption}\n{url}".strip() if caption else url
    data = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": False}).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp_data = resp.read()
            res_str = resp_data.decode("utf-8") if isinstance(resp_data, bytes) else str(resp_data)
            result = cast(dict[str, Any], json.loads(res_str))
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"[WARN] Failed to send Telegram URL: {e}", file=sys.stderr)
        return False


def send_telegram_buttons(
    token: str, chat_id: str, text: str, buttons: list[dict[str, str]], proxy: str | None = None
) -> bool:
    """Send inline keyboard buttons via Telegram sendMessage API."""
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    keyboard: list[list[dict[str, str]]] = []
    btn_list = buttons
    for btn in btn_list:
        btn_type = btn.get("type", "url")
        if btn_type == "url":
            keyboard.append([{"text": btn.get("text", ""), "url": btn.get("url", "")}])
        elif btn_type == "callback":
            keyboard.append([{"text": btn.get("text", ""), "callback_data": btn.get("callback_data", "")}])

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": keyboard}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp_data = resp.read()
            res_str = resp_data.decode("utf-8") if isinstance(resp_data, bytes) else str(resp_data)
            result = cast(dict[str, Any], json.loads(res_str))
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"[WARN] Failed to send Telegram buttons: {e}", file=sys.stderr)
        return False


def send_telegram_commands(
    token: str,
    commands: list[dict[str, str]],
    scope: dict[str, Any] | None = None,
    language_code: str = "",
    proxy: str | None = None
) -> bool:
    """Register bot commands via Telegram setMyCommands API."""
    api_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    payload: dict[str, Any] = {"commands": commands}
    if scope:
        payload["scope"] = scope
    if language_code:
        payload["language_code"] = language_code

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with get_opener(proxy).open(req, timeout=10) as resp:
            resp_data = resp.read()
            res_str = resp_data.decode("utf-8") if isinstance(resp_data, bytes) else str(resp_data)
            result = cast(dict[str, Any], json.loads(res_str))
            return bool(result.get("ok", False))
    except Exception as e:
        print(f"[WARN] Failed to set Telegram commands: {e}", file=sys.stderr)
        return False


# ── Process outboxes ──────────────────────────────────────────────────────────

def dispatch_outbox_item(token: str, item: dict[str, Any], proxy: str | None = None) -> bool:
    """Dispatch a single outbox item according to its type field."""
    item_type = item.get("type", "TELEGRAM_REPLY")
    chat_id = str(item.get("chat_id", ""))
    content = str(item.get("content", ""))

    if not chat_id:
        print(f"[WARN] Outbox item missing chat_id: {item}", file=sys.stderr)
        return False

    if item_type == "TELEGRAM_REPLY":
        return send_telegram_ack(token, chat_id, content, proxy)
    elif item_type == "TELEGRAM_SEND_DOCUMENT":
        file_path = item.get("file_path", content)
        caption = str(item.get("caption", ""))
        return send_telegram_document(token, chat_id, file_path, caption, proxy)
    elif item_type == "TELEGRAM_SEND_PHOTO":
        photo_path = item.get("photo_path", content)
        caption = str(item.get("caption", ""))
        return send_telegram_photo(token, chat_id, photo_path, caption, proxy)
    elif item_type == "TELEGRAM_SEND_URL":
        url = str(item.get("url", content))
        caption = str(item.get("caption", ""))
        return send_telegram_url(token, chat_id, url, caption, proxy)
    elif item_type == "TELEGRAM_SEND_BUTTONS":
        buttons = cast(list[dict[str, str]], item.get("buttons", []))
        return send_telegram_buttons(token, chat_id, content, buttons, proxy)
    elif item_type == "TELEGRAM_SEND_COMMANDS":
        commands = cast(list[dict[str, str]], item.get("commands", []))
        scope = cast(dict[str, Any] | None, item.get("scope"))
        lang = str(item.get("language_code", ""))
        return send_telegram_commands(token, commands, scope, lang, proxy)
    else:
        print(f"[WARN] Unknown outbox item type: {item_type}", file=sys.stderr)
        return False


def process_project_outboxes(token: str, proxy: str | None = None) -> None:
    """Scan all registered project outbox.json files and dispatch pending items."""
    registry = load_projects_registry()
    projects: list[dict[str, Any]] = cast(list[dict[str, Any]], registry.get("projects", []))

    for p in projects:
        inbox_target = resolve_project_inbox(p)
        if not inbox_target:
            continue
        project_root, _ = inbox_target
        outbox_file = project_root / ".agents" / "state" / "telegram" / "outbox.json"

        if not outbox_file.exists():
            continue

        raw_queue: list[dict[str, Any]] = []
        try:
            with open(outbox_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    raw_queue = cast(list[dict[str, Any]], data)
                elif isinstance(data, dict):
                    raw_queue = [cast(dict[str, Any], data)]
        except Exception as e:
            print(f"[WARN] Failed to read outbox {outbox_file}: {e}", file=sys.stderr)
            continue

        if not raw_queue:
            continue

        remaining: list[dict[str, Any]] = []
        sent_count = 0
        archive: list[dict[str, Any]] = []

        for item in raw_queue:
            if dispatch_outbox_item(token, item, proxy):
                sent_count += 1
                item["sent_at"] = utc_timestamp()
                archive.append(item)
            else:
                remaining.append(item)

        if sent_count > 0:
            tmp_outbox = outbox_file.with_name("outbox.json.tmp")
            try:
                with open(tmp_outbox, "w", encoding="utf-8") as f:
                    json.dump(remaining, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                os.replace(tmp_outbox, outbox_file)
            except Exception as e:
                print(f"[WARN] Failed to update outbox after send: {e}", file=sys.stderr)

            if archive:
                sent_log = outbox_file.parent / "sent_history.jsonl"
                try:
                    with open(sent_log, "a", encoding="utf-8") as f:
                        for item in archive:
                            f.write(json.dumps(item, ensure_ascii=False) + "\n")
                except Exception as e:
                    print(f"[WARN] Failed to write sent_history.jsonl: {e}", file=sys.stderr)


__all__ = [
    "send_telegram_ack",
    "send_telegram_document",
    "send_telegram_photo",
    "send_telegram_url",
    "send_telegram_buttons",
    "send_telegram_commands",
    "dispatch_outbox_item",
    "process_project_outboxes",
]
