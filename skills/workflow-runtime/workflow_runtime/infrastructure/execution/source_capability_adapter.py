"""Composition adapter to the canonical or installed gate aggregate."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from workflow_runtime.application.ports.source_capability import IssueRequest, IssueResult


class _Repository(Protocol):
    project_id: str

    def approved_scope(self, blueprint: str) -> tuple[dict[str, str], tuple[str, ...]]: ...


class GateSourceCapabilityAdapter:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        candidates = [self.root, *Path(__file__).resolve().parents]
        target = next((base / prefix / 'source_gate/__init__.py' for base in candidates
                       for prefix in ('tools/aiwf-hooks', '.agents/aiwf-hooks')
                       if (base / prefix / 'source_gate/__init__.py').is_file()), None)
        if target is None:
            raise ValueError('DEPENDENCY_UNAVAILABLE')
        name = '_aiwf_gate_' + hashlib.sha256(str(target).encode()).hexdigest()[:16]
        spec = importlib.util.spec_from_file_location(name, target, submodule_search_locations=[str(target.parent)])
        if spec is None or spec.loader is None:
            raise ValueError('DEPENDENCY_UNAVAILABLE')
        module = sys.modules.get(name)
        if module is None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        factory = cast(Callable[[Path], _Repository], getattr(module, 'JsonCapabilityRepository'))
        self.repository = factory(self.root)
        self.issuer = cast(Callable[[Path, IssueRequest], IssueResult], getattr(module, 'issue_capability'))

    def request(self, blueprint: str, work_item: str, owner: str, session: str, now: int) -> IssueRequest:
        hashes, scope = self.repository.approved_scope(blueprint)
        return IssueRequest(self.repository.project_id, work_item, 'implementation', blueprint, hashes[blueprint],
                            hashes, f'.agents/state/work-items/{work_item}/approvals.json',
                            f'BLUEPRINT-APPROVAL-{work_item}', scope, owner, session, now)

    def issue(self, request: IssueRequest) -> IssueResult:
        result = self.issuer(self.root, request)
        return IssueResult(result.issued, result.receipt_path, result.receipt, result.reason)
