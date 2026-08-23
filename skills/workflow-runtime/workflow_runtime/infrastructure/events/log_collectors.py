from __future__ import annotations

import logging
import os
import platform
import threading
from abc import ABC, abstractmethod
from typing import Any, Optional, cast

from workflow_runtime.infrastructure.events.event_bus import (RuntimeEvent,
                                                               RuntimeEventBus)

logger = logging.getLogger(__name__)


class BaseLogCollector(ABC):
    """
    Abstract base for IDE log file tail collectors.
    """

    POLL_INTERVAL_SEC: float = 2.0

    def __init__(self, event_bus: RuntimeEventBus, config: Optional[dict[str, Any]] = None) -> None:
        self._bus = event_bus
        self._config: dict[str, Any] = config or {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_byte_pos: int = 0
        self._current_file: Optional[str] = None

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return canonical provider name."""

    @abstractmethod
    def _detect_log_file(self) -> Optional[str]:
        """Return the absolute path to the log file to tail."""

    @abstractmethod
    def _parse_log_line(self, line: str) -> Optional[dict[str, Any]]:
        """Parse a single log line."""

    def _get_event_type(self) -> str:
        return f"{self.get_provider_name()}.log_line"

    def _get_conversation_id(self) -> str:
        return str(self._config.get("conversation_id", "unknown"))

    def start_tailing(self, conversation_id: Optional[str] = None) -> bool:
        if conversation_id:
            self._config["conversation_id"] = conversation_id

        log_file = self._detect_log_file()
        if not log_file:
            logger.warning(
                "%s: No log file detected — tailing not started.",
                self.get_provider_name()
            )
            return False

        self._current_file = log_file
        self._stop_event.clear()

        try:
            with open(log_file, "rb") as f:
                f.seek(0, 2)
                self._last_byte_pos = f.tell()
        except OSError:
            self._last_byte_pos = 0

        self._thread = threading.Thread(
            target=self._tail_loop,
            name=f"LogCollector-{self.get_provider_name()}",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "%s: Started tailing %s from byte %d",
            self.get_provider_name(), log_file, self._last_byte_pos
        )
        return True

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None
        logger.info("%s: Log collector stopped.", self.get_provider_name())

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def get_current_file(self) -> Optional[str]:
        return self._current_file

    def _tail_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._read_new_lines()
            except Exception as exc:
                logger.warning("%s: tail_loop error: %s", self.get_provider_name(), exc)

            self._stop_event.wait(self.POLL_INTERVAL_SEC)

    def _read_new_lines(self) -> None:
        if not self._current_file or not os.path.exists(self._current_file):
            return

        try:
            with open(self._current_file, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._last_byte_pos)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    self._last_byte_pos = f.tell()
                    line = line.rstrip("\n\r")
                    if not line.strip():
                        continue

                    event_data = self._parse_log_line(line)
                    if event_data is not None:
                        event = RuntimeEvent.create(
                            conversation_id=self._get_conversation_id(),
                            provider=self.get_provider_name(),
                            event_type=self._get_event_type(),
                            event_data=event_data,
                        )
                        self._bus.emit(event)

        except PermissionError:
            logger.warning("%s: Permission denied reading %s", self.get_provider_name(), self._current_file)
        except OSError as exc:
            logger.warning("%s: OS error reading log: %s", self.get_provider_name(), exc)


class AntigravityLogCollector(BaseLogCollector):
    _ENV_VAR = "ANTIGRAVITY_BRAIN_ROOT"
    _DEFAULT_BRAIN_ROOT = os.path.join(
        os.path.expanduser("~"), ".gemini", "antigravity-ide", "brain"
    )
    _TRANSCRIPT_REL = os.path.join(".system_generated", "logs", "transcript.jsonl")

    def get_provider_name(self) -> str:
        return "antigravity"

    def _get_event_type(self) -> str:
        return "antigravity.transcript_line"

    def _get_brain_root(self) -> str:
        override = os.environ.get(self._ENV_VAR, "")
        if override and os.path.isabs(override):
            return override
        return str(self._config.get("brain_root", self._DEFAULT_BRAIN_ROOT))

    def _detect_log_file(self) -> Optional[str]:
        conv_id = self._config.get("conversation_id")
        brain_root = self._get_brain_root()

        if conv_id:
            candidate = os.path.join(brain_root, str(conv_id), self._TRANSCRIPT_REL)
            if os.path.exists(candidate):
                return candidate

        try:
            latest: Optional[str] = None
            latest_mtime = 0.0
            if os.path.isdir(brain_root):
                for name in os.listdir(brain_root):
                    candidate = os.path.join(brain_root, name, self._TRANSCRIPT_REL)
                    if os.path.exists(candidate):
                        mtime = os.path.getmtime(candidate)
                        if mtime > latest_mtime:
                            latest_mtime = mtime
                            latest = candidate
            return latest
        except OSError:
            return None

    def _parse_log_line(self, line: str) -> Optional[dict[str, Any]]:
        import json as _json
        try:
            obj = cast(dict[str, Any], _json.loads(line))
            if bool(obj):
                return {
                    "step_index": obj.get("step_index"),
                    "source": str(obj.get("source", "")),
                    "type": str(obj.get("type", "")),
                    "raw": line[:200],
                }
            return None
        except (_json.JSONDecodeError, TypeError):
            return None


class ClaudeCodeLogCollector(BaseLogCollector):
    def get_provider_name(self) -> str:
        return "claude_code"

    def _get_event_type(self) -> str:
        return "claude_code.log_line"

    def _detect_log_file(self) -> Optional[str]:
        override = str(self._config.get("log_path") or os.environ.get("CLAUDE_LOG_PATH", ""))
        if override and os.path.exists(override):
            return override

        system = platform.system()
        candidates: list[str] = []

        if system == "Windows":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
            candidates = [
                os.path.join(base, "Claude", "logs", "claude_code.log"),
                os.path.join(base, "Claude", "logs", "mcp.log"),
            ]
        elif system == "Darwin":
            home = os.path.expanduser("~")
            candidates = [
                os.path.join(home, "Library", "Logs", "Claude", "claude_code.log"),
                os.path.join(home, "Library", "Logs", "Claude", "mcp.log"),
            ]
        else:
            home = os.path.expanduser("~")
            candidates = [
                os.path.join(home, ".config", "Claude", "logs", "claude_code.log"),
                os.path.join(home, ".local", "share", "Claude", "logs", "claude_code.log"),
            ]

        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _parse_log_line(self, line: str) -> Optional[dict[str, Any]]:
        import json as _json
        try:
            obj = cast(dict[str, Any], _json.loads(line))
            if bool(obj):
                return {
                    "level": str(obj.get("level", "info")),
                    "message_type": str(obj.get("type", "")),
                    "model": str(obj.get("model", "")),
                    "raw": line[:200],
                }
            return None
        except (_json.JSONDecodeError, TypeError):
            level = "info"
            if "ERROR" in line.upper():
                level = "error"
            elif "WARN" in line.upper():
                level = "warning"
            return {
                "level": level,
                "message_type": "plain",
                "model": "",
                "raw": line[:200],
            }


def build_collectors(
    event_bus: RuntimeEventBus,
    config: Optional[dict[str, Any]] = None,
) -> list[BaseLogCollector]:
    cfg = config or {}
    ag_cfg = cast(dict[str, Any], cfg.get("antigravity", {})) if isinstance(cfg.get("antigravity"), dict) else {}
    cc_cfg = cast(dict[str, Any], cfg.get("claude_code", {})) if isinstance(cfg.get("claude_code"), dict) else {}

    return [
        AntigravityLogCollector(event_bus=event_bus, config=ag_cfg),
        ClaudeCodeLogCollector(event_bus=event_bus, config=cc_cfg),
    ]


__all__ = [
    "BaseLogCollector",
    "AntigravityLogCollector",
    "ClaudeCodeLogCollector",
    "build_collectors",
]
