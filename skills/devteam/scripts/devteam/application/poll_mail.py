"""PollMailUseCase — return unread envelopes; advance cursor exactly-once."""

from __future__ import annotations

from ..domain.mailbox.envelope import Envelope
from ..domain.ports import MailboxRepository


class PollMailUseCase:
    def __init__(self, mailbox: MailboxRepository) -> None:
        self._mailbox = mailbox

    def execute(self, slug: str, advance: bool = True) -> list[Envelope]:
        cur = self._mailbox.cursor(slug)
        new = self._mailbox.read_from(slug, cur)  # parses each line (drift-safe)
        if advance and new:
            self._mailbox.set_cursor(slug, cur + len(new))
        return new
