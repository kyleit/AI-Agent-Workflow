"""Client configuration from env MSGBUS_* + CLI overrides, plus cipher factory."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..domain.identity import generate_vietnamese_name
from ..domain.ports import MessageCipher


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

    secure = bool(getattr(args, "tls", False)) or _is_true(os.environ.get("MSGBUS_TLS", "")) or bool(p.get("tls"))
    host = pick("host", "MSGBUS_HOST", "host", "127.0.0.1")
    port = int(pick("port", "MSGBUS_PORT", "port", 443 if secure else 8787))
    token = pick("token", "MSGBUS_TOKEN", "token", "changeme")
    sender = pick("sender", "MSGBUS_FROM", "from", "") or generate_vietnamese_name()
    e2ee_key = pick("e2ee_key", "MSGBUS_E2EE_KEY", "e2ee_key", None) or None
    return ClientConfig(host=host, port=port, token=token, sender=sender, e2ee_key=e2ee_key, secure=secure)


def save_profile(config: ClientConfig, save_sender: bool = False) -> Path:
    """Persist a connection profile so future sessions join with no env/flags."""
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"host": config.host, "port": config.port, "tls": config.secure, "token": config.token}
    if config.e2ee_key:
        data["e2ee_key"] = config.e2ee_key
    if save_sender and config.sender:
        data["from"] = config.sender
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)  # token inside — restrict on POSIX
    except OSError:
        pass
    return path


def build_cipher(config: ClientConfig) -> MessageCipher:
    from ..security.cipher import NullCipher, PskCipher

    return PskCipher(config.e2ee_key) if config.e2ee_key else NullCipher()
