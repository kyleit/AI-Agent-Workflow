"""Application values and the persistence boundary."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .domain import CapabilitySnapshot, PathDecision, RepoPath, SourceOperation


@dataclass(frozen=True)
class SourceChange:
    path: RepoPath
    operation: SourceOperation
    old_path: RepoPath | None = None


@dataclass(frozen=True)
class BatchDecision:
    all_allowed: bool
    decisions: tuple[PathDecision, ...]


@dataclass(frozen=True)
class IssueRequest:
    project_id: str
    work_item_id: str
    phase: str
    blueprint_path: str
    blueprint_sha256: str
    artifact_hashes: Mapping[str, str]
    approval_path: str
    approval_id: str
    scope: tuple[str, ...]
    owner_id: str
    session_id: str
    now: int


@dataclass(frozen=True)
class IssueResult:
    issued: bool
    receipt_path: str
    receipt: Mapping[str, object]
    reason: str


class CapabilityRepository(Protocol):
    def load_snapshot(self, work_item_id: str | None) -> CapabilitySnapshot:
        raise NotImplementedError

    def publish(self, request: IssueRequest) -> IssueResult:
        raise NotImplementedError

    def contains(self, path: RepoPath) -> bool: ...
