"""Layered client configuration and stable project/conversation identity."""
from __future__ import annotations

import json
import os
import platform as system_platform
import re
import shlex
import socket
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.identity import generate_vietnamese_name
from ..domain.ports import MessageCipher

DEFAULT_MSGBUS_HOST = "msgbus.klexpress.net"
STATE_COMMANDS = {"daemon", "pop-event", "ack-event", "release-event"}


def _is_true(value) -> bool:
    return str(value).lower() in ("1", "true", "yes", "on")


def project_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True,
            text=True, timeout=5, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd().resolve()


def profile_path() -> Path:
    override = os.environ.get("MSGBUS_CONFIG")
    return Path(override) if override else project_root() / ".agents" / "msgbus.json"


def _read_profile(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    if not isinstance(value, dict):
        raise ValueError("MsgBus profile must be a JSON object")
    return value


def load_profile() -> dict:
    try:
        global_profile = _read_profile(Path.home() / ".aiwf" / "msgbus.json")
    except RuntimeError:
        global_profile = {}
    return {**global_profile, **_read_profile(profile_path())}


def _app_name(root: Path) -> str:
    if os.environ.get("APP_NAME"):
        return os.environ["APP_NAME"]
    try:
        lines = (root / ".env").read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return root.name
    for line in lines:
        key, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and key.strip() == "APP_NAME":
            parts = shlex.split(value, comments=True)
            return " ".join(parts) or root.name
    return root.name


def validate_conversation(value: str) -> str:
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10))
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value)
            or value.endswith(".") or value.split(".")[0].upper() in reserved):
        raise ValueError("Invalid conversation ID; use a safe stable session ID")
    return value


def _label_part(value: object, limit: int) -> str:
    text = str(value).strip()
    if len(text) > limit or any(ord(char) < 32 for char in text):
        raise ValueError("Identity field is too long or contains control characters")
    return text


@dataclass
class ClientConfig:
    host: str
    port: int
    token: str
    sender: str
    e2ee_key: str | None
    secure: bool = False
    capabilities: tuple[str, ...] = ()
    avatar: str = ""
    identity: str = "AI agent"
    soul: str = "Collaborate clearly and leave verifiable handoffs."
    machine: str = ""
    platform: str = ""
    project: str = ""
    conversation_id: str = ""
    agent_name: str = ""
    root: Path = field(default_factory=Path.cwd)

    @property
    def base_url(self) -> str:
        return f"{'https' if self.secure else 'http'}://{self.host}:{self.port}"

    @property
    def conversation_short(self) -> str:
        return self.conversation_id[:4]

    @property
    def display_label(self) -> str:
        return f"[{self.project} | {self.platform} | #{self.conversation_short}] {self.agent_name}"

    @property
    def room(self) -> str:
        values = set(self.capabilities)
        if values & {"code", "frontend", "backend", "build", "security", "test"}:
            return "build"
        return "ops" if values & {"infra", "monitor"} else "lounge"

    def metadata(self) -> dict:
        return {
            "agent_name": self.agent_name, "project": self.project,
            "conversation_id": self.conversation_id,
            "conversation_short": self.conversation_short,
            "platform": self.platform, "machine": self.machine,
            "capabilities": ",".join(self.capabilities), "room": self.room,
            "avatar": self.avatar, "identity": self.identity, "soul": self.soul,
            "display_label": self.display_label,
        }

    def runtime_dir(self) -> Path:
        identity = validate_conversation(self.conversation_id)
        base = self.root / ".agents" / "state" / "msgbus"
        target = base / identity
        if target.resolve().parent != base.resolve():
            raise ValueError("Conversation state escapes its project root")
        return target


def load_config(args) -> ClientConfig:
    root = project_root()
    profile = load_profile()

    def pick(attr, env, key, default=None):
        value = getattr(args, attr, None)
        if value is not None:
            return value
        if env in os.environ:
            return os.environ[env]
        return profile[key] if key in profile else default

    host = str(pick("host", "MSGBUS_HOST", "host", DEFAULT_MSGBUS_HOST))
    secure = _is_true(pick("tls", "MSGBUS_TLS", "tls", host == DEFAULT_MSGBUS_HOST))
    port = int(pick("port", "MSGBUS_PORT", "port", 443 if secure else 8787))
    if not 0 < port < 65536:
        raise ValueError("Invalid MsgBus port")
    harness_id = next((os.environ[k] for k in (
        "CODEX_THREAD_ID", "CLAUDE_CONVERSATION_ID", "CONVERSATION_ID", "SESSION_ID"
    ) if os.environ.get(k)), "")
    conversation = str(pick("conversation_id", "MSGBUS_CONVERSATION_ID", "conversation_id", harness_id))
    if conversation:
        validate_conversation(conversation)
    if getattr(args, "command", "") in STATE_COMMANDS and not conversation:
        raise ValueError("This command requires --conversation-id or a supported session environment ID")
    role = _label_part(pick("role", "MSGBUS_ROLE", "role", os.environ.get("AI_AGENT_ROLE", "Agent")), 120)
    platform_name = _label_part(pick("platform", "MSGBUS_PLATFORM", "platform", system_platform.system()), 40)
    platform_name = "macOS" if platform_name == "Darwin" else platform_name
    raw = pick("capabilities", "MSGBUS_CAPABILITIES", "capabilities", [])
    values = raw if isinstance(raw, list) else str(raw).split(",")
    capabilities = tuple(dict.fromkeys(_label_part(x, 64).lower() for x in values if str(x).strip()))
    if len(capabilities) > 32:
        raise ValueError("At most 32 capabilities are allowed")
    config = ClientConfig(
        host=host, port=port, token=str(pick("token", "MSGBUS_TOKEN", "token", "changeme")),
        sender=str(pick("sender", "MSGBUS_FROM", "from", "")),
        e2ee_key=pick("e2ee_key", "MSGBUS_E2EE_KEY", "e2ee_key") or None,
        secure=secure, capabilities=capabilities,
        avatar=_label_part(pick("avatar", "MSGBUS_AVATAR", "avatar", ""), 8),
        identity=_label_part(pick("identity", "MSGBUS_IDENTITY", "identity", role), 120),
        soul=_label_part(pick("soul", "MSGBUS_SOUL", "soul", "Collaborate clearly and leave verifiable handoffs."), 280),
        machine=_label_part(pick("machine", "MSGBUS_MACHINE", "machine", socket.gethostname()), 80),
        platform=platform_name, project=_label_part(pick("project", "MSGBUS_PROJECT", "project", _app_name(root)), 120),
        conversation_id=conversation, agent_name=role, root=root,
    )
    if not config.sender:
        config.sender = config.display_label if conversation else generate_vietnamese_name()
    config.sender = _label_part(config.sender, 400)
    return config


def save_profile(config: ClientConfig, save_sender: bool = False) -> Path:
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _read_profile(path)
    data.update(host=config.host, port=config.port, tls=config.secure, token=config.token,
                capabilities=list(config.capabilities), role=config.agent_name,
                avatar=config.avatar, identity=config.identity, soul=config.soul)
    if config.e2ee_key:
        data["e2ee_key"] = config.e2ee_key
    if save_sender:
        data["from"] = config.sender
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def build_cipher(config: ClientConfig) -> MessageCipher:
    from ..security.cipher import NullCipher, PskCipher
    return PskCipher(config.e2ee_key) if config.e2ee_key else NullCipher()
