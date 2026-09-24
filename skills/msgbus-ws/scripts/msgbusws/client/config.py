"""Client configuration from env MSGBUS_* + CLI overrides, plus cipher factory."""
from __future__ import annotations

import json
import os
import platform as system_platform
import socket
from dataclasses import dataclass
from pathlib import Path

from ..domain.identity import generate_vietnamese_name
from ..domain.ports import MessageCipher

DEFAULT_MSGBUS_HOST = "msgbus.klexpress.net"


def _is_true(value) -> bool:
    return str(value).lower() in ("1", "true", "yes", "on")


def profile_path() -> Path:
    """Saved connection profile — lives under the aiwf home (~/.aiwf/msgbus.json)."""
    override = os.environ.get("MSGBUS_CONFIG")
    return Path(override) if override else Path.home() / ".aiwf" / "msgbus.json"


def load_profile() -> dict:
    try:
        return json.loads(profile_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@dataclass
class ClientConfig:
    host: str
    port: int
    token: str
    sender: str
    e2ee_key: str | None
    secure: bool = False  # TLS: https + wss (e.g. behind a k8s Ingress on a domain)
    capabilities: tuple[str, ...] = ()
    avatar: str = ""
    identity: str = "AI agent"
    soul: str = "Collaborate clearly and leave verifiable handoffs."
    machine: str = ""
    platform: str = ""

    @property
    def base_url(self) -> str:
        return f"{'https' if self.secure else 'http'}://{self.host}:{self.port}"


def load_config(args) -> ClientConfig:
    """Resolve config with precedence: CLI flag > env var > profile file > default."""
    p = load_profile()

    def pick(attr, env, key, default=None):
        val = getattr(args, attr, None)
        if val not in (None, ""):
            return val
        if os.environ.get(env):
            return os.environ[env]
        if p.get(key) not in (None, ""):
            return p[key]
        return default

    host = pick("host", "MSGBUS_HOST", "host", DEFAULT_MSGBUS_HOST)
    # The managed public endpoint is TLS-first. Explicit local hosts still
    # default to plain HTTP, and CLI/env/profile values retain precedence.
    secure = (
        bool(getattr(args, "tls", False))
        or _is_true(os.environ.get("MSGBUS_TLS", ""))
        or bool(p.get("tls"))
        or host == DEFAULT_MSGBUS_HOST
    )
    port = int(pick("port", "MSGBUS_PORT", "port", 443 if secure else 8787))
    token = pick("token", "MSGBUS_TOKEN", "token", "changeme")
    sender = pick("sender", "MSGBUS_FROM", "from", "") or generate_vietnamese_name()
    e2ee_key = pick("e2ee_key", "MSGBUS_E2EE_KEY", "e2ee_key", None) or None
    raw_capabilities = pick("capabilities", "MSGBUS_CAPABILITIES", "capabilities", "")
    if isinstance(raw_capabilities, list):
        capability_items = raw_capabilities
    else:
        capability_items = str(raw_capabilities).split(",")
    capabilities = tuple(
        str(item).strip()[:64]
        for item in capability_items[:32]
        if str(item).strip()
    )
    avatar = str(pick("avatar", "MSGBUS_AVATAR", "avatar", ""))[:8]
    identity = str(pick("identity", "MSGBUS_IDENTITY", "identity", "AI agent"))[:120]
    soul = str(pick(
        "soul",
        "MSGBUS_SOUL",
        "soul",
        "Collaborate clearly and leave verifiable handoffs.",
    ))[:280]
    machine = str(pick("machine", "MSGBUS_MACHINE", "machine", socket.gethostname()))[:80]
    platform_name = str(pick(
        "platform",
        "MSGBUS_PLATFORM",
        "platform",
        system_platform.system() or "Unknown",
    ))[:40]
    return ClientConfig(
        host=host,
        port=port,
        token=token,
        sender=sender,
        e2ee_key=e2ee_key,
        secure=secure,
        capabilities=capabilities,
        avatar=avatar,
        identity=identity,
        soul=soul,
        machine=machine,
        platform=platform_name,
    )


def save_profile(config: ClientConfig, save_sender: bool = False) -> Path:
    """Persist a connection profile so future sessions join with no env/flags."""
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"host": config.host, "port": config.port, "tls": config.secure, "token": config.token}
    if config.e2ee_key:
        data["e2ee_key"] = config.e2ee_key
    if save_sender and config.sender:
        data["from"] = config.sender
    if config.capabilities:
        data["capabilities"] = list(config.capabilities)
    if config.avatar:
        data["avatar"] = config.avatar
    data["identity"] = config.identity
    data["soul"] = config.soul
    data["machine"] = config.machine
    data["platform"] = config.platform
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)  # token inside — restrict on POSIX
    except OSError:
        pass
    return path


def build_cipher(config: ClientConfig) -> MessageCipher:
    from ..security.cipher import NullCipher, PskCipher

    return PskCipher(config.e2ee_key) if config.e2ee_key else NullCipher()
