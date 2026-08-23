"""SendMailUseCase — validate + atomically append an envelope to a seat inbox."""

from __future__ import annotations

from ..domain.errors import DevTeamError, ErrorCode
from ..domain.mailbox.envelope import Envelope
from ..domain.ports import Clock, IdGenerator, MailboxRepository, RosterRepository
from .dto import SendMailRequest


class SendMailUseCase:
    def __init__(
        self,
        roster: RosterRepository,
        mailbox: MailboxRepository,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._roster = roster
        self._mailbox = mailbox
        self._clock = clock
        self._ids = ids

    def execute(self, req: SendMailRequest) -> Envelope:
        if not self._roster.exists():
            raise DevTeamError(ErrorCode.NOT_INITIALIZED, "run 'devteam init --apply' first")
        roster = self._roster.load()
        roster.by_slug(req.to)  # raises UNKNOWN_SEAT if the recipient does not exist
        p = req.payload or {}
        env = Envelope(
            id=self._ids.next_id(req.frm),
            frm=req.frm,
            to=req.to,
            ts=self._clock.now_iso(),
            type=req.type,
            task_id=str(p.get("task_id", "")),
            title=str(p.get("title", "")),
            body=str(p.get("body", "")),
            state=str(p.get("state", "")),
            evidence=str(p.get("evidence", "")),
        ).validate()
        self._mailbox.ensure_inbox(req.to)
        self._mailbox.append(req.to, env)
        return env
