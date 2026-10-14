"""Verified item-local JSON capabilities with atomic publication."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import tempfile
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from .domain import Capability, CapabilitySnapshot, CapabilityStatus, RepoPath
from .ports import IssueRequest, IssueResult


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def read_json(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('CAPABILITY_INVALID')
    return cast(dict[str, object], value)


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(dict(value), stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def item_id(value: str) -> str:
    if not re.fullmatch(r'(?:FEAT|FIX|QUICK)-[0-9]+', value):
        raise ValueError('CONTEXT_MISMATCH')
    return value


def timestamp(value: object) -> int:
    if not isinstance(value, str):
        raise ValueError('CAPABILITY_INVALID')
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('CAPABILITY_INVALID')
    return int(parsed.timestamp())


class JsonCapabilityRepository:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.items = self.root / '.agents/state/work-items'
        self.project_id = hashlib.sha256(os.path.normcase(str(self.root)).encode()).hexdigest()
        self.windows = os.name == 'nt'
        self.diagnostics: dict[str, str] = {}

    @property
    def scoped(self) -> bool:
        return (self.root / '.agents/state/source-capability-mode.json').exists() or any(
            self.items.glob('*/implementation-entry-receipt.json'))

    def path(self, relative: str) -> Path:
        lexical = RepoPath(relative, windows=self.windows)
        path = self.root / lexical.value
        if not self.contains(lexical):
            raise ValueError('SCOPE_INVALID')
        return path

    def contains(self, path: RepoPath) -> bool:
        candidate = self.root / path.value
        if self.windows and any(part.rstrip(' .') != part or part.split('.')[0].upper() in
                                {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
                                for part in path.value.split('/')):
            return False
        try:
            resolved = candidate.resolve()
            return resolved != self.root and self.root in resolved.parents and not candidate.is_dir()
        except (OSError, RuntimeError, ValueError):
            return False

    def _parser(self, filename: str, symbol: str) -> object:
        candidates = [self.root, *Path(__file__).resolve().parents]
        for base in candidates:
            for prefix in ('skills', '.agents/skills'):
                path = base / prefix / 'strict-code-block-gate/scripts' / filename
                if not path.is_file():
                    continue
                spec = importlib.util.spec_from_file_location('aiwf_scope_' + path.stem, path)
                if spec is None or spec.loader is None:
                    break
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return cast(object, getattr(module, symbol))
        raise ValueError('DEPENDENCY_UNAVAILABLE')

    def approved_scope(self, blueprint: str) -> tuple[dict[str, str], tuple[str, ...]]:
        master = self.path(blueprint)
        if not re.match(r'^docs/(?:features/.+/blueprints/|blueprints/)', blueprint) or not master.is_file():
            raise ValueError('APPROVAL_MISMATCH')
        phases = cast(Callable[[Path], list[Path]], self._parser('run_strict_code_block_gate.py', 'discover_phase_paths'))
        matrix = cast(Callable[[Path], tuple[list[dict[str, str]], list[str]]],
                      self._parser('validate_artifact_set_code_blocks.py', 'extract_file_matrix_entries'))
        artifacts = [master, *phases(master)]
        hashes: dict[str, str] = {}
        scope: dict[str, str] = {}
        identity = re.search(r'(?:FEAT|FIX|QUICK)-[0-9]+', master.name)
        if identity is None:
            raise ValueError('APPROVAL_MISMATCH')
        for artifact in artifacts:
            relative = artifact.resolve().relative_to(self.root).as_posix()
            self.path(relative)
            text = artifact.read_text(encoding='utf-8-sig')
            match = re.search(r'^(?:feature_id|issue_id|quick_id|work_item_id):\s*(\S+)', text, re.MULTILINE)
            if not match or match.group(1) != identity.group(0):
                raise ValueError('APPROVAL_MISMATCH')
            hashes[relative] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if re.search(r'^status:\s*DEPENDENCY_DELIVERED\s*$', text, re.MULTILINE):
                continue
            entries, errors = matrix(artifact)
            if errors:
                raise ValueError('SCOPE_INVALID')
            for row in entries:
                value = row['file'].strip('`')
                path = RepoPath(value, windows=self.windows)
                if not self.contains(path):
                    raise ValueError('SCOPE_INVALID')
                scope[path.key] = path.value
        return hashes, tuple(sorted(scope.values()))

    def _approval(self, request: IssueRequest, bind: bool = False) -> dict[str, object]:
        item = item_id(request.work_item_id)
        expected = f'.agents/state/work-items/{item}/approvals.json'
        if request.approval_path != expected or request.project_id != self.project_id:
            raise ValueError('APPROVAL_MISMATCH')
        data = read_json(self.path(expected))
        raw = data.get('blueprint')
        if not isinstance(raw, dict):
            raise ValueError('APPROVAL_MISMATCH')
        bp = cast(dict[str, object], raw)
        if (bp.get('approved') is not True or bp.get('work_item_id') != item
                or bp.get('path') != request.blueprint_path or bp.get('sha256') != request.blueprint_sha256
                or not bp.get('approved_by') or not bp.get('approved_at')
                or request.approval_id != f'BLUEPRINT-APPROVAL-{item}'):
            raise ValueError('APPROVAL_MISMATCH')
        hashes, scope = self.approved_scope(request.blueprint_path)
        master_identity = re.search(r'^(?:feature_id|issue_id|quick_id|work_item_id):\s*(\S+)',
                                    self.path(request.blueprint_path).read_text(encoding='utf-8-sig'), re.MULTILINE)
        if master_identity is None or master_identity.group(1) != item:
            raise ValueError('APPROVAL_MISMATCH')
        if (hashes != dict(request.artifact_hashes) or tuple(sorted(request.scope)) != scope
                or hashes.get(request.blueprint_path) != request.blueprint_sha256):
            raise ValueError('APPROVAL_MISMATCH')
        digest = canonical_hash(list(scope))
        binding = {'artifact_hashes': hashes, 'scope_sha256': digest, 'approval_id': request.approval_id,
                   'owner_id': request.owner_id, 'session_id': request.session_id}
        if any(key in bp and bp[key] != value for key, value in binding.items()):
            raise ValueError('APPROVAL_MISMATCH')
        if not bind and any(bp.get(key) != value for key, value in binding.items()):
            raise ValueError('APPROVAL_MISMATCH')
        gp = f'docs/aiwf-runs/{item}/05-blueprint/code-block-gate.json'
        gate = read_json(self.path(gp))
        if (gate.get('decision') != 'PASS' or gate.get('authority') != 'strict-code-block-gate'
                or gate.get('blueprint_full_sha256') != request.blueprint_sha256
                or str(gate.get('blueprint_path', request.blueprint_path)).replace('\\', '/') != request.blueprint_path
                or gate.get('workflow_id', item) != item
                or gate.get('blocking_findings')):
            raise ValueError('APPROVAL_MISMATCH')
        workflow = read_json(self.path(f'.agents/state/work-items/{item}/workflow.json'))
        if (workflow.get('active_workflow') != item or workflow.get('active_phase') != request.phase
                or request.phase not in {'implementation', 'debug', 'verification'}
                or workflow.get('status') not in {'IN_PROGRESS', 'ACTIVE', 'WAITING_INPUT'}):
            raise ValueError('ENTRY_BLOCKED')
        if bind:
            bp.update(binding)
            data['blueprint'] = bp
            atomic_json(self.path(expected), data)
        return {'code_block_gate_path': gp, 'code_block_gate_sha256': hashlib.sha256(self.path(gp).read_bytes()).hexdigest()}

    def _record(self, path: Path) -> Capability:
        before = path.read_bytes()
        data = read_json(path)
        if (data.get('schema_version') != 'aiwf.source-capability/1'
                or data.get('work_item_id') != path.parent.name
                or data.get('content_hash') != canonical_hash({k: v for k, v in data.items() if k != 'content_hash'})):
            raise ValueError('CAPABILITY_INVALID')
        raw_scope = data['write_scope']
        raw_hashes = data['artifact_hashes']
        if not isinstance(raw_scope, list) or not all(isinstance(p, str) for p in cast(list[object], raw_scope)) or not isinstance(raw_hashes, dict):
            raise ValueError('CAPABILITY_INVALID')
        scope = tuple(cast(list[str], raw_scope))
        hashes = cast(dict[str, str], raw_hashes)
        issued = timestamp(data['issued_at'])
        expiry = timestamp(data['expires_at'])
        if (expiry - issued != 86400 or type(data.get('revision')) is not int or int(str(data['revision'])) < 1
                or not isinstance(data.get('capability_id'), str) or not data['capability_id']
                or list(scope) != sorted(set(scope))):
            raise ValueError('CAPABILITY_INVALID')
        request = IssueRequest(str(data['project_id']), str(data['work_item_id']), str(data['implementation_phase']),
                               str(data['blueprint_path']), str(data['blueprint_sha256']), hashes,
                               str(data['approval_path']), str(data['approval_id']), scope,
                               str(data['owner_id']), str(data['session_id']), issued)
        evidence_paths = [request.approval_path, f'.agents/state/work-items/{request.work_item_id}/workflow.json',
                          str(data['code_block_gate_path']), *hashes]
        observations = {relative: self.path(relative).read_bytes() for relative in evidence_paths}
        valid = True
        try:
            gate = self._approval(request)
            valid = all(data.get(k) == v for k, v in gate.items()) and data.get('scope_sha256') == canonical_hash(list(scope))
        except (OSError, ValueError, KeyError, TypeError):
            valid = False
        return Capability(request.work_item_id, request.project_id, CapabilityStatus(str(data['status'])), request.phase,
                          tuple(RepoPath(p, windows=self.windows) for p in scope), request.owner_id, request.session_id,
                          issued, expiry, valid, before == path.read_bytes() and all(
                              self.path(relative).read_bytes() == observed for relative, observed in observations.items()))

    def revoke(self, work_item_id: str) -> None:
        path = self.path(f'.agents/state/work-items/{item_id(work_item_id)}/implementation-entry-receipt.json')
        lock = path.with_suffix('.lock')
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
        try:
            data = read_json(path)
            data['status'] = 'REVOKED'
            data['revision'] = int(str(data['revision'])) + 1
            data.pop('content_hash', None)
            data['content_hash'] = canonical_hash(data)
            atomic_json(path, data)
        finally:
            lock.unlink()

    def load_snapshot(self, work_item_id: str | None) -> CapabilitySnapshot:
        if work_item_id is not None:
            item_id(work_item_id)
        records: list[Capability] = []
        self.diagnostics.clear()
        for path in sorted(self.items.glob('*/implementation-entry-receipt.json')):
            try:
                record = self._record(path)
                if not record.snapshot_consistent:
                    record = self._record(path)
                records.append(record)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.diagnostics[path.parent.name] = str(exc)
        return CapabilitySnapshot(tuple(records))

    def publish(self, request: IssueRequest) -> IssueResult:
        relative = f'.agents/state/work-items/{request.work_item_id}/implementation-entry-receipt.json'
        lock: Path | None = None
        try:
            item_id(request.work_item_id)
            path = self.path(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = path.with_suffix('.lock')
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            lock = lock_path
            os.close(fd)
            gate = self._approval(request, bind=True)
            approved = read_json(self.path(request.approval_path))['blueprint']
            epoch = str(cast(dict[str, object], approved).get('approved_at', ''))
            previous = read_json(path) if path.exists() else {}
            fresh_approval = bool(previous) and previous.get('approval_epoch') != epoch
            if previous.get('status') in {'REVOKED', 'CANCELLED', 'COMPLETED'} and not fresh_approval:
                raise ValueError('CAPABILITY_INACTIVE')
            if previous and any(previous.get(k) != v for k, v in {
                'owner_id': request.owner_id, 'session_id': request.session_id,
                'approval_id': request.approval_id, 'artifact_hashes': dict(request.artifact_hashes),
                'scope_sha256': canonical_hash(sorted(request.scope))}.items()) and not fresh_approval:
                raise ValueError('APPROVAL_MISMATCH')
            value: dict[str, object] = {
                'schema_version': 'aiwf.source-capability/1', 'capability_id': (previous.get('capability_id') if not fresh_approval else None) or uuid.uuid4().hex,
                'approval_epoch': epoch,
                'project_id': request.project_id, 'work_item_id': request.work_item_id, 'status': 'ACTIVE',
                'implementation_phase': request.phase, 'blueprint_path': request.blueprint_path,
                'blueprint_sha256': request.blueprint_sha256, 'artifact_hashes': dict(request.artifact_hashes),
                'approval_path': request.approval_path, 'approval_id': request.approval_id,
                'write_scope': sorted(request.scope), 'scope_sha256': canonical_hash(sorted(request.scope)),
                'owner_id': request.owner_id, 'session_id': request.session_id,
                'issued_at': datetime.fromtimestamp(request.now, timezone.utc).isoformat(),
                'expires_at': datetime.fromtimestamp(request.now + 86400, timezone.utc).isoformat(),
                'revision': int(str(previous.get('revision', 0))) + 1, **gate}
            value['content_hash'] = canonical_hash(value)
            atomic_json(self.root / '.agents/state/source-capability-mode.json', {'schema_version': 'aiwf.source-capability-mode/1', 'activated': True})
            atomic_json(path, value)
            return IssueResult(True, relative, value, 'ISSUED')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return IssueResult(False, relative, {}, 'SNAPSHOT_CHANGED' if isinstance(exc, FileExistsError) else str(exc))
        finally:
            if lock is not None:
                lock.unlink()
