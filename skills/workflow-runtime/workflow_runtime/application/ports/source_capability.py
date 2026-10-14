"""Workflow-owned capability request; independent of the gate implementation."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


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


class SourceCapabilityPort(Protocol):
    def issue(self, request: IssueRequest) -> IssueResult:
        raise NotImplementedError
