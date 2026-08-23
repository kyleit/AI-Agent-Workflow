"""Composition root — the ONLY place infrastructure is wired into use cases (DI).

Both the CLI and the MCP server build their use cases here, so business logic
never depends on concrete adapters directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..application.acquire_lock import AcquireLockUseCase
from ..application.enter_seat import EnterSeatUseCase
from ..application.init_team import InitTeamUseCase
from ..application.leave_seat import LeaveSeatUseCase
from ..application.list_locks import ListLocksUseCase
from ..application.poll_mail import PollMailUseCase
from ..application.release_lock import ReleaseLockUseCase
from ..application.render_board import RenderBoardUseCase
from ..application.send_mail import SendMailUseCase
from ..infrastructure.paths import PathResolver
from ..infrastructure.repositories.board_repo import FileBoardRepository
from ..infrastructure.repositories.lock_repo import FileLockRepository
from ..infrastructure.repositories.mailbox_repo import JsonlMailboxRepository
from ..infrastructure.repositories.roster_repo import FileRosterRepository
from ..infrastructure.repositories.seat_state_repo import FileSeatStateRepository
from ..infrastructure.scanning.repo_scanner import TopLevelRepoScanner
from ..infrastructure.system.clock import SystemClock
from ..infrastructure.system.git_status import GitCliStatusProvider
from ..infrastructure.system.idgen import UlidIdGenerator


@dataclass
class Container:
    init: InitTeamUseCase
    enter: EnterSeatUseCase
    leave: LeaveSeatUseCase
    send: SendMailUseCase
    poll: PollMailUseCase
    board: RenderBoardUseCase
    acquire_lock: AcquireLockUseCase
    release_lock: ReleaseLockUseCase
    list_locks: ListLocksUseCase
    paths: PathResolver


def build_container(root: str | None = None) -> Container:
    resolved = root or PathResolver.discover_root()
    paths = PathResolver(resolved)

    roster = FileRosterRepository(paths)
    mailbox = JsonlMailboxRepository(paths)
    state = FileSeatStateRepository(paths)
    board = FileBoardRepository(paths)
    locks = FileLockRepository(paths)
    scanner = TopLevelRepoScanner(paths)
    clock = SystemClock()
    ids = UlidIdGenerator()
    git = GitCliStatusProvider(paths.root)

    poll = PollMailUseCase(mailbox)
    return Container(
        init=InitTeamUseCase(roster, mailbox, state, board, scanner, clock, paths.project_id()),
        enter=EnterSeatUseCase(roster, state, git, clock, poll),
        leave=LeaveSeatUseCase(roster, state, board, clock),
        send=SendMailUseCase(roster, mailbox, clock, ids),
        poll=poll,
        board=RenderBoardUseCase(roster, state, board, locks, clock),
        acquire_lock=AcquireLockUseCase(roster, locks, clock),
        release_lock=ReleaseLockUseCase(locks),
        list_locks=ListLocksUseCase(locks, clock),
        paths=paths,
    )
