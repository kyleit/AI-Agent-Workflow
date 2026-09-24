"""Secret masking for provider configuration shown in CLI output or logs.

This is the single masking implementation for ``aiwf provider`` (CLI output,
``list_providers``, the Obsidian README); do not add a second one.
"""

from __future__ import annotations

from typing import Any, cast

SECRET_KEY_MARKERS: tuple[str, ...] = ("key", "token", "password", "secret", "credential")
MASK: str = "********"


def _is_secret_key(key: Any) -> bool:
    lowered = str(key).lower()
    return any(marker in lowered for marker in SECRET_KEY_MARKERS)


def mask_secrets(config: Any) -> Any:
    """Return a copy of ``config`` with every non-empty value under a secret-looking key masked.

    The whole value is replaced, whatever its type: a dict or list stored under
    ``credentials`` could hold secrets under innocuous keys, so it is not walked.
    Empty values are kept so an unset secret stays visible as unset.
    """
    if isinstance(config, dict):
        masked: dict[str, Any] = {}
        for key, value in cast(dict[str, Any], config).items():
            if _is_secret_key(key):
                masked[key] = MASK if value else value
            else:
                masked[key] = mask_secrets(value)
        return masked
    if isinstance(config, list):
        return [mask_secrets(item) for item in cast(list[Any], config)]
    return config


__all__ = ["MASK", "SECRET_KEY_MARKERS", "mask_secrets"]
