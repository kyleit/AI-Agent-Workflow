"""Stable composition root for source authorization."""
from __future__ import annotations

import time
from collections.abc import Sequence
from pathlib import Path

from . import capabilities
from .domain import ActorContext as ActorContext, SourceOperation as SourceOperation, evaluate_path as evaluate_path
from .ports import BatchDecision, IssueRequest as IssueRequest, IssueResult, SourceChange as SourceChange
from .repository import JsonCapabilityRepository


def authorize_paths(root: Path, changes: Sequence[SourceChange], actor: ActorContext) -> BatchDecision:
    return capabilities.authorize_paths(changes, actor, JsonCapabilityRepository(root), int(time.time()))


def issue_capability(root: Path, request: IssueRequest) -> IssueResult:
    return capabilities.issue_capability(request, JsonCapabilityRepository(root))
