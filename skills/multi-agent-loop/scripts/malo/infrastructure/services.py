"""Infrastructure services: clock, mailbox, and the loop-engine CLI adapter.

`LoopEngineCli` is the concrete `LoopEnginePort`: it shells the loop-controller
engine (single source of truth for transitions) and narrows its JSON output
without `Any` (basedpyright strict-full).
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from malo.application.dto import DecisionRequest, DecisionView
from malo.domain.errors import MaloError
from malo.domain.jsonutil import as_json_object, as_object_list, as_object_mapping


class SystemClock:
    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class FileMailbox:
    """Minimal shared-workspace handoff log (append-only)."""

    def post(self, root: Path, workflow_id: str, sender: str, note: str) -> None:
        mail_dir = root / ".agents" / "session-mail"
        mail_dir.mkdir(parents=True, exist_ok=True)
        path = mail_dir / f"{workflow_id}.log"
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            _ = handle.write(f"{ts} [{sender}] {note}\n")


def _get_str(data: Mapping[str, object], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


def _get_bool(data: Mapping[str, object], key: str) -> bool:
    value = data.get(key)
    return value if isinstance(value, bool) else False


def _get_str_tuple(data: Mapping[str, object], key: str) -> tuple[str, ...]:
    return tuple(
        item for item in as_object_list(data.get(key)) if isinstance(item, str)
    )


def _resolve_python() -> list[str]:
    for candidate in (["python3"], ["python"], ["py", "-3"]):
        try:
            probe = subprocess.run(
                [*candidate, "-c", "import sys"],
                capture_output=True, check=False,
            )
        except FileNotFoundError:
            continue
        if probe.returncode == 0:
            return candidate
    raise MaloError(
        "No python3/python/py interpreter found to run the loop-controller engine."
    )


class LoopEngineCli:
    """Shell the loop-controller engine (loop_engine) via subprocess."""

    def __init__(self, root: Path, loop_scripts_dir: Path) -> None:
        self._root = root
        self._scripts = loop_scripts_dir
        self._python = _resolve_python()

    def _run(self, args: list[str], stdin_text: str | None = None) -> str:
        import os

        env = dict(os.environ)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{self._scripts}{os.pathsep}{existing}" if existing else str(self._scripts)
        )
        completed = subprocess.run(
            [*self._python, "-m", "loop_engine", *args],
            cwd=str(self._root),
            input=stdin_text,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            raise MaloError(
                f"loop_engine {args[0]} failed (exit {completed.returncode}): "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        return completed.stdout

    def decide(self, request: DecisionRequest) -> DecisionView:
        args = [
            "decide",
            "--repo-root", str(self._root),
            "--workflow", request.workflow_id,
            "--phase", request.phase,
            "--verdict", request.verdict.value,
        ]
        for finding in request.findings:
            args += ["--finding", finding]
        if request.next_phase:
            args += ["--next-phase", request.next_phase]
        if request.backtrack_target:
            args += ["--backtrack-target", request.backtrack_target]
        if request.is_terminal_phase:
            args.append("--terminal")
        if request.requires_approval:
            args.append("--requires-approval")
        if request.approval_present:
            args.append("--approval-present")

        stdout = self._run(args)
        payload = as_json_object(stdout)
        if payload is None:
            raise MaloError("loop_engine decide did not return an object.")
        decision = as_object_mapping(payload.get("decision"))
        return DecisionView(
            transition=_get_str(decision, "transition"),
            resulting_phase=_get_str(decision, "resulting_phase"),
            stop_conditions_met=_get_str_tuple(decision, "stop_conditions_met"),
            escalate=_get_bool(decision, "escalate"),
            persist_payload_json=stdout,
        )

    def persist(self, payload_json: str) -> str:
        args = ["persist", "--repo-root", str(self._root), "--input", "-"]
        payload = as_json_object(self._run(args, stdin_text=payload_json))
        if payload is None:
            raise MaloError("loop_engine persist did not return an object.")
        return _get_str(payload, "state_path")
