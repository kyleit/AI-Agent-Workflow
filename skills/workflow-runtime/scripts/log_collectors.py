# log_collectors.py
# IDE Log Collectors for FEAT-048 Phase 4 — Task 4.2
# Extends BaseLogCollector for Antigravity IDE and Claude Code
# Per blueprint: AntigravityLogCollector + ClaudeCodeLogCollector
from __future__ import annotations

import logging
import os
import platform
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from event_bus import RuntimeEvent, RuntimeEventBus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BaseLogCollector
# ---------------------------------------------------------------------------

class BaseLogCollector(ABC):
    """
    Abstract base for IDE log file tail collectors.

    Implements a background-thread tail loop that:
    1. Detects the target log file path.
    2. Emits RuntimeEvents via the bus when new content is detected.
    3. Respects start_tailing() / stop() lifecycle.
    """

    # Polling interval for tail loop (seconds)
    POLL_INTERVAL_SEC: float = 2.0

    def __init__(self, event_bus: RuntimeEventBus, config: dict = None):
        """
        Args:
            event_bus: RuntimeEventBus to emit events to.
            config: Optional provider-specific configuration overrides.
        """
        self._bus = event_bus
        self._config = config or {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_byte_pos: int = 0
        self._current_file: Optional[str] = None

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return canonical provider name (e.g. 'antigravity')."""

    @abstractmethod
    def _detect_log_file(self) -> Optional[str]:
        """
        Return the absolute path to the log file to tail, or None if not found.
        Must not raise.
        """

    @abstractmethod
    def _parse_log_line(self, line: str) -> Optional[dict]:
        """
        Parse a single log line and return a dict for event_data, or None to skip.
        Must not raise.
        """

    def _get_event_type(self) -> str:
        """Return event_type string for emitted events."""
        return f"{self.get_provider_name()}.log_line"

    def _get_conversation_id(self) -> str:
        """Return current conversation_id for emitted events. Override if dynamic."""
        return self._config.get("conversation_id", "unknown")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_tailing(self, conversation_id: Optional[str] = None) -> bool:
        """
        Start background tail thread.

        Args:
            conversation_id: Optional conversation ID to tag events with.

        Returns:
            True if started successfully, False if log file not found.
        """
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

        # Seek to EOF on start to tail only new content
        try:
            with open(log_file, "rb") as f:
                f.seek(0, 2)  # seek to end
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
        """Stop the tail thread gracefully."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None
        logger.info("%s: Log collector stopped.", self.get_provider_name())

    def is_running(self) -> bool:
        """Return True if the tail thread is active."""
        return self._thread is not None and self._thread.is_alive()

    def get_current_file(self) -> Optional[str]:
        """Return path of the currently tailed file."""
        return self._current_file

    # ------------------------------------------------------------------
    # Internal tail loop
    # ------------------------------------------------------------------

    def _tail_loop(self) -> None:
        """Background thread: poll log file for new content."""
        while not self._stop_event.is_set():
            try:
                self._read_new_lines()
            except Exception as exc:
                logger.warning("%s: tail_loop error: %s", self.get_provider_name(), exc)

            self._stop_event.wait(self.POLL_INTERVAL_SEC)

    def _read_new_lines(self) -> None:
        """Read any new lines appended since last byte position."""
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


# ---------------------------------------------------------------------------
# AntigravityLogCollector
# ---------------------------------------------------------------------------

class AntigravityLogCollector(BaseLogCollector):
    """
    Log collector for Antigravity IDE.

    Tails: {BRAIN_ROOT}/{conversation_id}/.system_generated/logs/transcript.jsonl

    Emits event_type: "antigravity.transcript_line"
    event_data: {"step_index": int, "source": str, "type": str, "raw": str}
    """

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
        return self._config.get("brain_root", self._DEFAULT_BRAIN_ROOT)

    def _detect_log_file(self) -> Optional[str]:
        """Detect transcript.jsonl for the configured conversation_id."""
        conv_id = self._config.get("conversation_id")
        brain_root = self._get_brain_root()

        if conv_id:
            candidate = os.path.join(brain_root, conv_id, self._TRANSCRIPT_REL)
            if os.path.exists(candidate):
                return candidate

        # Fallback: find most recently modified transcript
        try:
            latest = None
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

    def _parse_log_line(self, line: str) -> Optional[dict]:
        """Parse a JSONL transcript line → event_data dict."""
        import json as _json
        try:
            obj = _json.loads(line)
            return {
                "step_index": obj.get("step_index"),
                "source": obj.get("source", ""),
                "type": obj.get("type", ""),
                "raw": line[:200],  # first 200 chars only — never expose full content
            }
        except (_json.JSONDecodeError, TypeError):
            return None


# ---------------------------------------------------------------------------
# ClaudeCodeLogCollector
# ---------------------------------------------------------------------------

class ClaudeCodeLogCollector(BaseLogCollector):
    """
    Log collector for Claude Code IDE.

    Detects log path OS-aware:
    - Windows: %APPDATA%/Claude/logs/claude_code.log
    - macOS:   ~/Library/Logs/Claude/claude_code.log
    - Linux:   ~/.config/Claude/logs/claude_code.log

    Emits event_type: "claude_code.log_line"
    event_data: {"level": str, "message_type": str, "model": str, "raw": str}
    """

    def get_provider_name(self) -> str:
        return "claude_code"

    def _get_event_type(self) -> str:
        return "claude_code.log_line"

    def _detect_log_file(self) -> Optional[str]:
        """Detect Claude Code log file OS-aware."""
        # Allow config override
        override = self._config.get("log_path") or os.environ.get("CLAUDE_LOG_PATH", "")
        if override and os.path.exists(override):
            return override

        system = platform.system()
        candidates: List[str] = []

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

    def _parse_log_line(self, line: str) -> Optional[dict]:
        """Parse Claude Code log line — try JSON first, then plain text."""
        import json as _json
        try:
            obj = _json.loads(line)
            return {
                "level": obj.get("level", "info"),
                "message_type": obj.get("type", ""),
                "model": obj.get("model", ""),
                "raw": line[:200],
            }
        except (_json.JSONDecodeError, TypeError):
            # Plain text log line — still emit but with minimal parsing
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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_collectors(
    event_bus: RuntimeEventBus,
    config: dict = None,
) -> List[BaseLogCollector]:
    """
    Build all enabled log collectors.

    Args:
        event_bus: Shared RuntimeEventBus.
        config: Optional dict with provider-specific configs:
                {"antigravity": {...}, "claude_code": {...}}

    Returns:
        List of BaseLogCollector instances (not yet started).
    """
    config = config or {}
    return [
        AntigravityLogCollector(event_bus=event_bus, config=config.get("antigravity", {})),
        ClaudeCodeLogCollector(event_bus=event_bus, config=config.get("claude_code", {})),
    ]
