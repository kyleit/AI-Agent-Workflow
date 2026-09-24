"""Application ports (interfaces) for dependency injection.

The application layer depends only on these abstractions; concrete subprocess,
filesystem, clock, and loop-engine adapters live in infrastructure and are
injected at composition time (presentation/cli.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from malo.application.dto import DecisionRequest, DecisionView, SpawnOutcome
from malo.domain.models import AgentRegistry
from malo.domain.results import PhaseRunResult


class AgentSpawner(Protocol):
    """Runs a headless agent command in the shared workspace."""

    def run(self, command: list[str], cwd: Path, timeout_s: int) -> SpawnOutcome:
        ...


class LoopEnginePort(Protocol):
    """Boundary to the loop-controller engine (the transition authority)."""

    def decide(self, request: DecisionRequest) -> DecisionView:
        ...

    def persist(self, payload_json: str) -> str:
        ...


class RegistryRepo(Protocol):
    """Loads the agent registry (aiwf.agent-registry/1)."""

    def load(self, root: Path) -> AgentRegistry:
        ...


class ResultRepo(Protocol):
    """Appends phase-run results (aiwf.phase-run/1) to the run ledger."""

    def append(self, root: Path, result: PhaseRunResult) -> str:
        ...


class MailboxPort(Protocol):
    """Optional cross-agent handoff note on the shared workspace."""

    def post(self, root: Path, workflow_id: str, sender: str, note: str) -> None:
        ...


class ApprovalExecutor(Protocol):
    """Records a real approval for a gate (auto mode). Returns True on success."""

    def approve(self, gate: str, workflow_id: str, root: Path) -> bool:
        ...


class Clock(Protocol):
    def now_iso(self) -> str:
        ...
