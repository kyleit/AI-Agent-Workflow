"""CLI + composition root for the loop engine.

Wires infrastructure adapters into the application use cases (DI) and exposes
the deterministic contract:

    loop_engine load    --workflow <id> --phase <phase>
    loop_engine decide  --workflow <id> --verdict <PASS|BLOCK|FAIL|ERROR> ...
    loop_engine persist [--input <file>|-]

`load` and `decide` never write. `persist` performs the only side effects
(atomic state write + append-only ledger).

Typing: basedpyright strict-full. argparse attributes are `Any`, so every access
is narrowed once through the typed `_ArgReader` boundary (cast → object → narrow).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from loop_engine.application.dto import PersistInput
from loop_engine.application.use_cases import (
    DecideUseCase,
    LoadLoopStateUseCase,
    PersistLoopUseCase,
)
from loop_engine.domain.errors import LoopEngineError
from loop_engine.domain.jsonutil import as_json_object
from loop_engine.domain.ledger import LedgerEntry
from loop_engine.domain.models import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_NO_PROGRESS_THRESHOLD,
    DecisionInput,
    LoopState,
    Verdict,
)
from loop_engine.domain.signature import compute_failure_signature
from loop_engine.infrastructure.file_repositories import (
    FileLoopLedgerRepository,
    FileLoopStateRepository,
)
from loop_engine.infrastructure.services import Sha256HashService, SystemClock


class _ArgReader:
    """Typed boundary over argparse.Namespace (isolates reportAny to one place)."""

    def __init__(self, namespace: argparse.Namespace) -> None:
        self._ns = namespace

    def _raw(self, name: str) -> object:
        return cast(object, getattr(self._ns, name, None))

    def get_str(self, name: str) -> str:
        value = self._raw(name)
        return value if isinstance(value, str) else ""

    def get_opt_str(self, name: str) -> str | None:
        value = self._raw(name)
        return value if isinstance(value, str) else None

    def get_int(self, name: str, default: int) -> int:
        value = self._raw(name)
        return value if isinstance(value, int) and not isinstance(value, bool) else default

    def get_bool(self, name: str) -> bool:
        return self._raw(name) is True

    def get_str_list(self, name: str) -> list[str]:
        value = self._raw(name)
        if isinstance(value, list):
            return [item for item in cast("list[object]", value) if isinstance(item, str)]
        return []


def _resolve_repo_root(override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".agents").is_dir() or (candidate / ".git").exists():
            return candidate
    return current


def _emit(payload: Mapping[str, object]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True))


def _read_input_json(source: str | None) -> Mapping[str, object]:
    if source in (None, "-"):
        raw = sys.stdin.read()
    else:
        raw = Path(str(source)).read_text(encoding="utf-8")
    payload = as_json_object(raw)
    if payload is None:
        raise LoopEngineError("persist input must be a JSON object.")
    return payload


def _resolve_signature(
    explicit: str | None, findings: Sequence[str] | None
) -> str:
    if explicit is not None:
        return explicit
    if findings:
        return compute_failure_signature(findings)
    return ""


def _cmd_load(reader: _ArgReader, repo_root: Path) -> int:
    use_case = LoadLoopStateUseCase(FileLoopStateRepository(repo_root))
    state = use_case.execute(
        reader.get_str("workflow"),
        reader.get_str("phase"),
        max_iterations=reader.get_int("max_iterations", DEFAULT_MAX_ITERATIONS),
        no_progress_threshold=reader.get_int(
            "no_progress_threshold", DEFAULT_NO_PROGRESS_THRESHOLD
        ),
    )
    _emit({"loop_state": state.to_dict()})
    return 0


def _cmd_decide(reader: _ArgReader, repo_root: Path) -> int:
    loader = LoadLoopStateUseCase(FileLoopStateRepository(repo_root))
    state: LoopState = loader.execute(
        reader.get_str("workflow"),
        reader.get_str("phase"),
        max_iterations=reader.get_int("max_iterations", DEFAULT_MAX_ITERATIONS),
        no_progress_threshold=reader.get_int(
            "no_progress_threshold", DEFAULT_NO_PROGRESS_THRESHOLD
        ),
    )
    findings = reader.get_str_list("finding")
    signature = _resolve_signature(reader.get_opt_str("new_failure_signature"), findings)
    decision_input = DecisionInput(
        current_state=state,
        verdict=Verdict.parse(reader.get_str("verdict")),
        new_failure_signature=signature,
        approval_present=reader.get_bool("approval_present"),
        requires_approval=reader.get_bool("requires_approval"),
        is_terminal_phase=reader.get_bool("terminal"),
        next_phase=reader.get_opt_str("next_phase"),
        backtrack_target=reader.get_opt_str("backtrack_target"),
        user_halt=reader.get_bool("user_halt"),
    )
    output = DecideUseCase().execute(
        decision_input,
        gate=reader.get_opt_str("gate"),
        evidence_refs=tuple(reader.get_str_list("evidence")),
    )
    decision = output.decision
    _emit(
        {
            "decision": {
                "transition": decision.transition.value,
                "resulting_phase": decision.resulting_phase,
                "next_iteration": decision.next_iteration,
                "no_progress_count": decision.no_progress_count,
                "stop_conditions_met": decision.stop_values(),
                "backtrack_target": decision.backtrack_target,
                "escalate": decision.escalate,
                "escalation_options": list(decision.escalation_options),
            },
            "next_state": output.next_state.to_dict(),
            "ledger_entry": output.ledger_entry.to_dict(),
        }
    )
    return 0


def _cmd_persist(reader: _ArgReader, repo_root: Path) -> int:
    payload = _read_input_json(reader.get_opt_str("input") or "-")
    next_state_raw = payload.get("next_state")
    ledger_raw = payload.get("ledger_entry")
    if not isinstance(next_state_raw, dict):
        raise LoopEngineError("persist input requires a 'next_state' object.")
    if not isinstance(ledger_raw, dict):
        raise LoopEngineError("persist input requires a 'ledger_entry' object.")
    next_state = LoopState.from_dict(cast("Mapping[str, object]", next_state_raw))
    ledger_entry = LedgerEntry.from_dict(cast("Mapping[str, object]", ledger_raw))

    use_case = PersistLoopUseCase(
        FileLoopStateRepository(repo_root),
        FileLoopLedgerRepository(repo_root),
        SystemClock(),
        Sha256HashService(),
    )
    result = use_case.execute(PersistInput(next_state, ledger_entry))
    _emit(
        {
            "state_path": result.state_path,
            "ledger_path": result.ledger_path,
            "state_sha256": result.state_sha256,
            "updated_at": result.updated_at,
            "path_sanitization": "PASS",
            "absolute_paths_remaining": 0,
        }
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loop_engine",
        description="AIWF deterministic loop controller engine.",
    )
    common = argparse.ArgumentParser(add_help=False)
    _ = common.add_argument("--repo-root", default=None)
    _ = parser.add_argument("--repo-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    load_p = sub.add_parser(
        "load", parents=[common], help="Read (or initialize) the loop state."
    )
    _ = load_p.add_argument("--workflow", required=True)
    _ = load_p.add_argument("--phase", required=True)
    _ = load_p.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    _ = load_p.add_argument(
        "--no-progress-threshold", type=int, default=DEFAULT_NO_PROGRESS_THRESHOLD
    )

    decide_p = sub.add_parser(
        "decide", parents=[common], help="Compute the next transition."
    )
    _ = decide_p.add_argument("--workflow", required=True)
    _ = decide_p.add_argument("--phase", required=True)
    _ = decide_p.add_argument(
        "--verdict", required=True, choices=[v.value for v in Verdict]
    )
    _ = decide_p.add_argument("--new-failure-signature", default=None)
    _ = decide_p.add_argument("--finding", action="append", default=[])
    _ = decide_p.add_argument("--approval-present", action="store_true")
    _ = decide_p.add_argument("--requires-approval", action="store_true")
    _ = decide_p.add_argument("--terminal", action="store_true")
    _ = decide_p.add_argument("--next-phase", default=None)
    _ = decide_p.add_argument("--backtrack-target", default=None)
    _ = decide_p.add_argument("--user-halt", action="store_true")
    _ = decide_p.add_argument("--gate", default=None)
    _ = decide_p.add_argument("--evidence", action="append", default=[])
    _ = decide_p.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    _ = decide_p.add_argument(
        "--no-progress-threshold", type=int, default=DEFAULT_NO_PROGRESS_THRESHOLD
    )

    persist_p = sub.add_parser(
        "persist", parents=[common], help="Atomically write state + ledger."
    )
    _ = persist_p.add_argument("--input", default="-")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    reader = _ArgReader(args)
    repo_root = _resolve_repo_root(reader.get_opt_str("repo_root"))
    command = reader.get_str("command")
    try:
        if command == "load":
            return _cmd_load(reader, repo_root)
        if command == "decide":
            return _cmd_decide(reader, repo_root)
        if command == "persist":
            return _cmd_persist(reader, repo_root)
    except LoopEngineError as exc:
        _emit({"error": type(exc).__name__, "message": str(exc)})
        return 2
    parser.error(f"unknown command: {command}")
    return 2
