"""Request/response DTOs crossing the application boundary."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SendMailRequest:
    to: str
    type: str
    payload: dict
    frm: str = "seat-leader"


@dataclass(frozen=True)
class EnterSeatResult:
    charter: str
    seat_state: str
    next_step_now: str
    new_mail: list
    git_status: str


@dataclass(frozen=True)
class InitResult:
    roster: dict
    files_written: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    applied: bool = False
