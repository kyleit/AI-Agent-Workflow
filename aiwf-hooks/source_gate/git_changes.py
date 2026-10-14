from __future__ import annotations
import json
import os
import re
import subprocess
from pathlib import Path
from .legacy import rel_posix
from collections.abc import Sequence
from typing import cast
from .domain import RepoPath, SourceOperation
from .ports import SourceChange


def git_output(root: Path, args: list[str]) -> str:
    try:
        top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=root, stdin=subprocess.DEVNULL,
                             capture_output=True, check=True, encoding='utf-8').stdout.strip()
        if Path(top).resolve() != root.resolve():
            raise ValueError('GIT_INSPECTION_FAILED')
        result = subprocess.run(['git', *args], cwd=root, stdin=subprocess.DEVNULL,
                                capture_output=True, check=True, encoding='utf-8')
        return result.stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError('GIT_INSPECTION_FAILED') from exc


def git_blob_oid(root: Path, path: str, content: bytes) -> str:
    try:
        result = subprocess.run(['git', 'hash-object', '--path', path, '--stdin'], cwd=root,
                                input=content, capture_output=True, check=True)
        return result.stdout.decode('utf-8').strip()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise ValueError('GIT_INSPECTION_FAILED') from exc


def _changes(value: str) -> tuple[SourceChange, ...]:
    fields = value.split('\0')
    result: list[SourceChange] = []
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        index += 1
        if status[0] not in 'ACDMRTUXB' or index >= len(fields) or not fields[index]:
            raise ValueError('GIT_INSPECTION_FAILED')
        old = RepoPath(fields[index], windows=os.name == 'nt')
        index += 1
        if status[0] in 'RC':
            if index >= len(fields) or not fields[index]:
                raise ValueError('GIT_INSPECTION_FAILED')
            new = RepoPath(fields[index], windows=os.name == 'nt')
            index += 1
            result.append(SourceChange(new, SourceOperation.RENAME, old))
        else:
            operation = SourceOperation.DELETE if status[0] == 'D' else SourceOperation.CREATE if status[0] == 'A' else SourceOperation.MODIFY
            result.append(SourceChange(old, operation, None))
    return tuple(result)


def staged_changes(root: Path) -> Sequence[SourceChange]:
    return _changes(git_output(root, ['diff', '--cached', '--name-status', '-z', '-M', '-C']))


def outgoing_pairs(root: Path, refs: Sequence[str]) -> tuple[tuple[str, SourceChange], ...]:
    pairs: list[tuple[str, SourceChange]] = []
    destination = os.environ.get('AIWF_PUSH_URL')
    excluded: list[str] = []
    if destination:
        tips: set[str] = set()
        # Fetch refs do not prove pushurl publication. Query the actual hook destination.
        for line in git_output(root, ['ls-remote', '--heads', '--', destination]).splitlines():
            fields = line.split('\t')
            if len(fields) != 2 or re.fullmatch('[0-9a-f]{40,64}', fields[0]) is None or not fields[1].startswith('refs/heads/'):
                raise ValueError('GIT_INSPECTION_FAILED')
            try:
                git_output(root, ['cat-file', '-e', fields[0] + '^{commit}'])
            except ValueError:
                continue  # Unknown local objects cannot hide any outgoing history.
            tips.add(fields[0])
        excluded = ['--not', *sorted(tips)] if tips else []
    for ref in refs:
        fields = ref.split()
        if len(fields) != 4:
            raise ValueError('GIT_INSPECTION_FAILED')
        local, remote = fields[1], fields[3]
        if not all(re.fullmatch('[0-9a-f]{40,64}', sha) for sha in (local, remote)):
            raise ValueError('GIT_INSPECTION_FAILED')
        if not local.strip('0'):
            continue
        revision = local if not remote.strip('0') else f'{remote}..{local}'
        for commit in git_output(root, ['rev-list', '--reverse', revision, *excluded]).splitlines():
            changes = _changes(git_output(root, ['diff-tree', '--root', '--no-commit-id', '--name-status', '-z', '-r', '-m', '-M', '-C', commit]))
            pairs.extend((commit, change) for change in changes)
    return tuple(pairs)


def outgoing_changes(root: Path, refs: Sequence[str]) -> Sequence[SourceChange]:
    return tuple(change for _, change in outgoing_pairs(root, refs))


def historical_owners(root: Path, commit: str, path: str) -> frozenset[str]:
    from .repository import JsonCapabilityRepository, canonical_hash
    repository = JsonCapabilityRepository(root)
    scoped = repository.scoped
    def accepts(value: object) -> set[str]:
        if isinstance(value, list):
            return set[str]().union(*(accepts(item) for item in cast(list[object], value)))
        if not isinstance(value, dict):
            return set()
        record = cast(dict[str, object], value)
        if record.get('status') in {'REVOKED', 'CANCELLED', 'BLOCKED', 'FAILED'}:
            return set()
        nested = set[str]().union(*(accepts(record.get(key)) for key in ('receipt', 'authorization', 'items', 'records')))
        identity = record.get('work_item_id', record.get('workflow_id'))
        exact = record.get('commit_sha', record.get('commit')) == commit
        authorized = record.get('authorized') is True or record.get('approved') is True
        paths = record.get('paths', record.get('allowed_files'))
        if scoped:
            released = record.get('schema_version') == 'aiwf.git-release-authorization/1'
            valid_identity = (r'(?:FEAT|FIX|QUICK)-[0-9]+|RELEASE-v[0-9]+\.[0-9]+\.[0-9]+'
                              if released else r'(?:FEAT|FIX|QUICK)-[0-9]+')
            if (record.get('schema_version') not in {'aiwf.git-authorization/1', 'aiwf.git-release-authorization/1'} or record.get('operation') != 'commit'
                    or record.get('project_id') != repository.project_id or record.get('status') != 'AUTHORIZED'
                    or not isinstance(identity, str) or re.fullmatch(valid_identity, identity) is None
                    or record.get('authorized') is not True or not isinstance(paths, list)
                    or not all(isinstance(p, str) for p in cast(list[object], paths))
                    or record.get('content_hash') != canonical_hash({k: v for k, v in record.items() if k != 'content_hash'})):
                return nested
            try:
                owned = [RepoPath(p, windows=os.name == 'nt').key for p in cast(list[str], paths)]
                canonical = RepoPath(path, windows=os.name == 'nt').key
            except ValueError:
                return set()
            if released and exact and canonical in owned:
                try:
                    proof = record.get('blob_oids')
                    if (not isinstance(proof, dict) or cast(dict[str, object], proof).get(path) != git_output(root, ['rev-parse', commit + ':' + path]).strip()
                            or re.fullmatch(r'[0-9a-f]{64}', str(record.get('release_authorization_sha256', ''))) is None
                            or re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', str(record.get('release_version', ''))) is None):
                        return nested
                except ValueError:
                    return nested
            return nested | ({identity} if exact and canonical in owned and len(set(owned)) == len(owned) else set())
        # Legacy commit-wide audit is exact to that commit, never to later edits.
        path_bound = isinstance(paths, list) and path in paths
        return nested | ({str(identity)} if exact and authorized and bool(identity) and (path_bound or (not scoped and paths is None)) else set())
    owners = frozenset[str]().union(*(accepts(value) for value in authorization_receipts(root)))
    if owners:
        return owners
    from .release import git_release_snapshot
    from .repository import atomic_json
    snapshot = git_release_snapshot(root, [path], commit)
    if snapshot is None:
        return owners
    record: dict[str, object] = {'schema_version': 'aiwf.git-release-authorization/1',
        'project_id': repository.project_id, 'operation': 'commit', 'status': 'AUTHORIZED', 'authorized': True,
        'commit_sha': commit, 'work_item_id': snapshot.owner, 'paths': [path], 'blob_oids': snapshot.blob_oids,
        'release_version': snapshot.version, 'release_authorization_sha256': snapshot.authorization_sha256}
    record['content_hash'] = canonical_hash(record)
    import hashlib
    name = hashlib.sha256(path.encode()).hexdigest()
    atomic_json(root / '.agents/state/audit' / ('release-' + commit + '-' + name + '.json'), record)
    return frozenset({snapshot.owner})


def history_authorizes(root: Path, commit: str, path: str) -> bool:
    return len(historical_owners(root, commit, path)) == 1


def is_commit_or_history_authorized(root: Path, file_path: str, local_sha: str, remote_sha: str) -> bool:
    refs = [f'refs/heads/probe {local_sha} refs/heads/probe {remote_sha or "0" * 40}']
    pairs = [(commit, change) for commit, change in outgoing_pairs(root, refs)
             if change.path.value == file_path or (change.old_path and change.old_path.value == file_path)]
    return bool(pairs) and all(change_history_authorized(root, commit, change) for commit, change in pairs)

def change_history_authorized(root: Path, commit: str, change: SourceChange) -> bool:
    endpoints = [change.path] + ([change.old_path] if change.old_path else [])
    owners = [historical_owners(root, commit, path.value) for path in endpoints]
    return all(len(values) == 1 for values in owners) and len(set[str]().union(*owners)) == 1

def git_lines(root: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(['git', *args], cwd=str(root), capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def outgoing_commits(root: Path, local_sha: str, remote_sha: str) -> list[str]:
    zero = '0' * 40
    if not local_sha or local_sha == zero:
        return []
    if not remote_sha or remote_sha == zero:
        return git_lines(root, ['rev-list', '--reverse', local_sha])
    return git_lines(root, ['rev-list', '--reverse', f'{remote_sha}..{local_sha}'])

def commit_parents(root: Path, commit_sha: str) -> list[str]:
    lines = git_lines(root, ['rev-list', '--parents', '-n', '1', commit_sha])
    return lines[0].split()[1:] if lines else []

def commit_touches_file(root: Path, commit_sha: str, file_path: str, *, merge: bool=False) -> bool:
    args = ['diff-tree', '--root', '--no-commit-id', '--name-only', '-r']
    if merge:
        args.append('-m')
    args.extend([commit_sha, '--', file_path])
    return rel_posix(root, file_path) in {rel_posix(root, value) for value in git_lines(root, args)}

def authorization_receipts(root: Path) -> list[object]:
    """Load only machine receipts from the two canonical audit locations."""
    values: list[object] = []
    locations = (root / '.agents' / 'state' / 'audit', root / 'docs' / 'aiwf-runs')
    for directory in locations:
        if not directory.is_dir():
            continue
        for path in directory.rglob('*'):
            if path.suffix.lower() not in {'.json', '.jsonl'} or not path.is_file():
                continue
            try:
                if path.suffix.lower() == '.jsonl':
                    values.extend((json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()))
                else:
                    values.append(json.loads(path.read_text(encoding='utf-8')))
            except (OSError, ValueError, TypeError):
                continue
    return values

def receipt_authorizes(value: object, commit_sha: str, active_work_item: str | None) -> bool:
    if isinstance(value, list):
        return any(receipt_authorizes(item, commit_sha, active_work_item) for item in cast(list[object], value))
    if not isinstance(value, dict):
        return False
    record = cast(dict[str, object], value)
    if any(receipt_authorizes(record.get(key), commit_sha, active_work_item) for key in ("receipt", "authorization", "approval", "items", "records")):
        return True
    item = record.get("work_item_id", record.get("workflow_id"))
    return (record.get("commit_sha", record.get("commit")) == commit_sha
            and (not active_work_item or item == active_work_item)
            and (record.get("authorized") is True or record.get("approved") is True))
