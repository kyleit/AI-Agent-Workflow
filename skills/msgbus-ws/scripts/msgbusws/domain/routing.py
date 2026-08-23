"""Channel routing rule (broadcast vs private/peer-to-peer). Pure domain logic."""
from __future__ import annotations

from .models import Message

BROADCAST_ALIASES = frozenset({"", "*", "all", "broadcast"})


def is_broadcast(to: str | None) -> bool:
    return not to or to.lower() in BROADCAST_ALIASES


def targets(message: Message, name: str) -> bool:
    """True if the subscriber `name` should receive `message`.

    Broadcast reaches everyone; a private message reaches only its recipient
    (`to == name`) and its author (`sender == name`, so the sender sees its own
    private traffic in catch-up).
    """
    if is_broadcast(message.to):
        return True
    return message.to == name or message.sender == name
