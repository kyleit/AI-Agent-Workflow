from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from workflow_runtime.shared.errors import DomainException


@dataclass(frozen=True)
class TelegramInboxEvent:
    event_id: str
    sender: str
    content: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])


class TelegramAdapter:
    """Infrastructure adapter for Telegram Bot API communication and inbox parsing."""

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        config_path: str = ".agents/config/.env.telegram-notify",
    ) -> None:
        self.config_path = config_path
        self._bot_token = bot_token or self.resolve_bot_token()
        self._chat_id = chat_id or self.resolve_chat_id()

    def resolve_bot_token(self) -> str:
        """Resolves bot token from os.environ first, fallback to config file."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if token:
            return token.strip()
        cfg_file = Path(self.config_path)
        if cfg_file.exists():
            try:
                with cfg_file.open(encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TELEGRAM_BOT_TOKEN="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except OSError:
                pass
        return ""

    def resolve_chat_id(self) -> str:
        """Resolves chat ID from os.environ first, fallback to config file."""
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if chat_id:
            return chat_id.strip()
        cfg_file = Path(self.config_path)
        if cfg_file.exists():
            try:
                with cfg_file.open(encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TELEGRAM_CHAT_ID="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except OSError:
                pass
        return ""

    def send_message(
        self,
        message: str,
        chat_id: str | None = None,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Sends Telegram notification POST request to Bot API.

        Raises:
            DomainException: If token is missing or API returns non-200 HTTP status.
        """
        token = self._bot_token or self.resolve_bot_token()
        target_chat_id = chat_id or self._chat_id or self.resolve_chat_id()

        if not token or not target_chat_id:
            raise DomainException(
                "Telegram bot_token or chat_id is missing from environment/config."
            )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            if isinstance(e, DomainException):
                raise
            raise DomainException(
                f"Failed to deliver Telegram notification: {str(e)}"
            ) from e

    def parse_inbox_event(self, event_data: dict[str, Any]) -> TelegramInboxEvent:
        """Validates and parses raw inbox JSON payload into TelegramInboxEvent DTO.

        Raises:
            DomainException: If required schema fields are missing.
        """
        required_fields = ["event_id", "sender", "content", "timestamp"]
        for field_name in required_fields:
            if field_name not in event_data:
                raise DomainException(
                    f"Missing required field '{field_name}' in Telegram inbox event payload."
                )

        raw_meta = event_data.get("metadata")
        meta = cast(dict[str, Any], raw_meta) if isinstance(raw_meta, dict) else {}

        return TelegramInboxEvent(
            event_id=str(event_data["event_id"]),
            sender=str(event_data["sender"]),
            content=str(event_data["content"]),
            timestamp=str(event_data["timestamp"]),
            metadata=meta,
        )


__all__ = [
    "TelegramInboxEvent",
    "TelegramAdapter",
]
