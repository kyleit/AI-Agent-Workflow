from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime
from typing import Any, cast

HUMAN_NAMES = [
    "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi",
    "Ivan", "Judy", "Mallory", "Nina", "Oscar", "Peggy", "Romeo", "Sybil",
    "Trent", "Victor", "Walter", "Zoe", "Alex", "Sam", "Jordan", "Taylor"
]


class MailService:
    def __init__(self) -> None:
        self.state_dir = os.path.join(".agents", "state")
        self.mail_dir = os.path.join(self.state_dir, "mail")
        self.registry_file = os.path.join(self.mail_dir, "registry.json")
        self.session_file = os.path.join(".agents", ".session.json")

        os.makedirs(self.mail_dir, exist_ok=True)
        if not os.path.exists(self.registry_file):
            with open(self.registry_file, 'w', encoding="utf-8") as f:
                json.dump({"sessions": {}}, f)

    def _load_registry(self) -> dict[str, Any]:
        try:
            with open(self.registry_file, 'r', encoding="utf-8") as f:
                raw_data = json.load(f)
                return cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {"sessions": {}}
        except Exception:
            return {"sessions": {}}

    def _save_registry(self, data: dict[str, Any]) -> None:
        with open(self.registry_file, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _get_current_session(self) -> tuple[str | None, str | None]:
        if not os.path.exists(self.session_file):
            return None, None
        try:
            with open(self.session_file, 'r', encoding="utf-8") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, dict):
                    d = cast(dict[str, Any], raw_data)
                    sid = str(d["session_id"]) if d.get("session_id") else None
                    sname = str(d["session_name"]) if d.get("session_name") else None
                    return sid, sname
        except Exception:
            pass
        return None, None

    def _set_current_session(self, session_id: str, name: str) -> None:
        data: dict[str, Any] = {}
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, dict):
                        data = cast(dict[str, Any], raw_data)
            except Exception:
                pass

        data["session_id"] = session_id
        data["session_name"] = name
        with open(self.session_file, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _resolve_session_id(self, identifier: str) -> str | None:
        registry = self._load_registry()
        raw_sessions = registry.get("sessions")
        sessions = cast(dict[str, Any], raw_sessions) if isinstance(raw_sessions, dict) else {}

        if identifier in sessions:
            return identifier

        for sid, info_raw in sessions.items():
            if isinstance(info_raw, dict):
                info = cast(dict[str, Any], info_raw)
                if info.get("name") == identifier:
                    return str(sid)

        return None

    def register(self) -> dict[str, Any]:
        registry = self._load_registry()
        raw_sessions = registry.get("sessions")
        sessions = cast(dict[str, Any], raw_sessions) if isinstance(raw_sessions, dict) else {}

        curr_id, _ = self._get_current_session()
        if curr_id and curr_id in sessions:
            info_raw = sessions[curr_id]
            info = cast(dict[str, Any], info_raw) if isinstance(info_raw, dict) else {}
            return {"session_id": curr_id, "session_name": str(info.get("name", ""))}

        new_id = str(uuid.uuid4())

        used_names: list[str] = []
        for info_raw in sessions.values():
            if isinstance(info_raw, dict):
                info = cast(dict[str, Any], info_raw)
                if info.get("name"):
                    used_names.append(str(info["name"]))

        attempts = 0
        new_name = random.choice(HUMAN_NAMES)
        while new_name in used_names and attempts < 100:
            if attempts > 20:
                new_name = f"{random.choice(HUMAN_NAMES)}-{random.randint(10, 99)}"
            else:
                new_name = random.choice(HUMAN_NAMES)
            attempts += 1

        sessions[new_id] = {
            "name": new_name,
            "registered_at": datetime.now().isoformat()
        }
        registry["sessions"] = sessions
        self._save_registry(registry)
        self._set_current_session(new_id, new_name)

        return {"session_id": new_id, "session_name": new_name}

    def list_sessions(self) -> dict[str, Any]:
        registry = self._load_registry()
        raw_sessions = registry.get("sessions")
        return cast(dict[str, Any], raw_sessions) if isinstance(raw_sessions, dict) else {}

    def send(self, to_identifier: str, message: str) -> bool:
        to_id = self._resolve_session_id(to_identifier)
        if not to_id:
            print(f"Error: Recipient '{to_identifier}' not found in registry.")
            return False

        from_id, from_name = self._get_current_session()
        if not from_id:
            from_id = "unknown"
            from_name = "Anonymous"

        mailbox_file = os.path.join(self.mail_dir, f"{to_id}.json")

        mailbox: list[dict[str, Any]] = []
        if os.path.exists(mailbox_file):
            try:
                with open(mailbox_file, 'r', encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        mailbox = cast(list[dict[str, Any]], raw_data)
            except Exception:
                mailbox = []

        mail_obj = {
            "from_id": from_id,
            "from_name": from_name,
            "to_id": to_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        mailbox.append(mail_obj)

        with open(mailbox_file, 'w', encoding="utf-8") as f:
            json.dump(mailbox, f, indent=2)

        return True

    def read(self) -> list[dict[str, Any]]:
        curr_id, _ = self._get_current_session()
        if not curr_id:
            print("Error: You must register a session first (`aiwf mail register`).")
            return []

        mailbox_file = os.path.join(self.mail_dir, f"{curr_id}.json")
        if not os.path.exists(mailbox_file):
            return []

        mailbox: list[dict[str, Any]] = []
        try:
            with open(mailbox_file, 'r', encoding="utf-8") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, list):
                    mailbox = cast(list[dict[str, Any]], raw_data)
        except Exception:
            return []

        with open(mailbox_file, 'w', encoding="utf-8") as f:
            json.dump([], f)

        return mailbox


__all__ = ["HUMAN_NAMES", "MailService"]
