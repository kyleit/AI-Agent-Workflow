from __future__ import annotations
from pathlib import Path
import sys
import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast
from .legacy import read_json, active_workflow_id, parse_iso, now, repo_file, sha256_file, report_pass, scope_digest, is_source_file, repo_root, is_aiwf_project
RELEASE_AUTH_REL = '.agents/state/release/authorization.json'


@dataclass(frozen=True)
class GitReleaseSnapshot:
    owner: str
    version: str
    authorization_sha256: str
    blob_oids: dict[str, str]


def git_release_snapshot(root: Path, paths: Sequence[str], commit: str | None = None,
                         *, expected_authorization_sha256: str | None = None) -> GitReleaseSnapshot | None:
    """Publication consent covers reviewed Git blobs, never source edit rights."""
    from .git_changes import git_blob_oid, git_output
    authorization = root / RELEASE_AUTH_REL
    if not paths:
        return None
    try:
        before = authorization.read_bytes()
        authorization_hash = hashlib.sha256(before).hexdigest()
        if expected_authorization_sha256 is not None and expected_authorization_sha256 != authorization_hash:
            return None
        raw: object = json.loads(before)
        if not _release_authorization_candidate_status(root, raw, list(paths))[0]:
            return None
        if not isinstance(raw, dict):
            return None
        candidate = cast(dict[str, object], raw)
        version = str(candidate.get('version', ''))
        if re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version) is None:
            return None
        owner = candidate.get('work_item')
        identity = str(owner) if owner else 'RELEASE-v' + version
        if re.fullmatch(r'(?:FEAT|FIX|QUICK)-[0-9]+|RELEASE-v[0-9]+\.[0-9]+\.[0-9]+', identity) is None:
            return None
        scope = candidate.get('scope')
        if not isinstance(scope, list) or not all(isinstance(p, str) for p in cast(list[object], scope)):
            return None
        captured: dict[str, bytes] = {}
        digest = hashlib.sha256()
        for relative in sorted(set(cast(list[str], scope))):
            source = repo_file(root, relative)
            if source is None:
                return None
            content = source.read_bytes()
            captured[relative] = content
            digest.update(relative.encode('utf-8') + b'\0' + hashlib.sha256(content).digest() + b'\n')
        if candidate.get('scope_sha256') != digest.hexdigest() or any(path not in captured for path in paths):
            return None
        if commit is not None and (commit != git_output(root, ['rev-parse', 'HEAD']).strip()
                or commit != git_output(root, ['rev-parse', 'refs/tags/v' + version + '^{commit}']).strip()):
            return None
        blobs: dict[str, str] = {}
        for path in paths:
            # Hash the captured approved bytes, not a potentially replaced worktree file.
            expected = git_blob_oid(root, path, captured[path])
            actual = git_output(root, ['rev-parse', (commit or '') + ':' + path]).strip()
            if expected != actual:
                return None
            blobs[path] = actual
        if authorization.read_bytes() != before or not _release_authorization_candidate_status(root, candidate, list(paths))[0]:
            return None
        return GitReleaseSnapshot(identity, version, authorization_hash, blobs)
    except (OSError, ValueError):
        return None

def release_authorization_status(root: Path, staged: list[str] | None=None) -> tuple[bool, str]:
    """Validate the short-lived authorization created for one release candidate."""
    path = root / RELEASE_AUTH_REL
    if not path.is_file():
        return (False, 'release authorization missing')
    candidate = read_json(path)
    return _release_authorization_candidate_status(root, candidate, staged)


def _release_authorization_candidate_status(root: Path, value: object, staged: list[str] | None = None) -> tuple[bool, str]:
    if not isinstance(value, dict):
        return (False, 'release authorization is not active')
    candidate = cast(dict[str, object], value)
    if candidate.get('authorized') is not True:
        return (False, 'release authorization is not active')
    if candidate.get('operation') != 'release':
        return (False, 'release authorization operation mismatch')
    active = active_workflow_id(root)
    release_mode = str(candidate.get('release_mode') or 'workflow')
    if release_mode == 'maintenance':
        if active or candidate.get('work_item') is not None:
            return (False, f'maintenance release authorization has active workflow {active}')
    elif not active or candidate.get('work_item') != active:
        return (False, f"release authorization work item mismatch (active={active or 'none'})")
    version = candidate.get('version')
    if not isinstance(version, str) or not version:
        return (False, 'release authorization version is missing')
    receipt_path = receipt_dir(root) / f'{version}.json'
    receipt_data = read_json(receipt_path)
    if not isinstance(receipt_data, dict) or receipt_data.get('version') != version:
        return (False, 'release authorization receipt is missing or stale')
    expires = candidate.get('expires_at')
    parsed_expiry = parse_iso(expires) if isinstance(expires, str) else None
    if parsed_expiry is None or parsed_expiry <= now():
        return (False, 'release authorization expired or invalid')
    if release_mode != 'maintenance':
        blueprint = candidate.get('blueprint_path')
        blueprint_path = repo_file(root, blueprint)
        if blueprint_path is None:
            return (False, 'release authorization Blueprint is missing')
        blueprint_hash = candidate.get('blueprint_sha256')
        if not isinstance(blueprint_hash, str) or blueprint_hash != sha256_file(blueprint_path):
            return (False, 'release authorization Blueprint hash is stale')
        if not report_pass(root, candidate.get('debug_path')) or not report_pass(root, candidate.get('verification_path')):
            return (False, 'release debug/verification evidence is not PASS')
    scope = candidate.get('scope')
    scope_paths: set[str] = {str(item).replace('\\', '/') for item in cast(list[object], scope) if isinstance(item, str)} if isinstance(scope, list) else set()
    if not scope_paths:
        return (False, 'release authorization scope is empty')
    if any((repo_file(root, relative) is None for relative in scope_paths)):
        return (False, 'release authorization scope contains an invalid repository path')
    if candidate.get('scope_sha256') != scope_digest(root, list(scope_paths)):
        return (False, 'release authorization scope hash is stale')
    if staged is not None:
        staged_source = {str(item).replace('\\', '/') for item in staged if is_source_file(root, item)}
        outside = sorted(staged_source - scope_paths)
        if outside:
            return (False, 'staged source files exceed release scope: ' + ', '.join(outside[:10]))
    subject = active or 'maintenance scope'
    return (True, f'verified release authorization for {subject}')

def receipt_dir(root: Path) -> Path:
    cfg = None
    for c in (root / 'release.config.json', root / '.agents' / 'release.config.json'):
        cfg = read_json(c)
        if isinstance(cfg, dict):
            break
    rel = (cfg or {}).get('receipt_dir', '.agents/state/release')
    return root / str(rel)

def cmd_check_release_tags(_args: argparse.Namespace) -> int:
    """Block pushing a v* tag that has no release receipt (pre-push backstop).

    stdin: git pre-push lines '<local ref> <local sha> <remote ref> <remote sha>'.
    A release must go through `python tools/release.py` (which writes the receipt).
    """
    root = repo_root()
    if not root or not is_aiwf_project(root):
        return 0
    from .commands import bypassed, BLOCK_BANNER
    if bypassed():
        return 0
    from .git_changes import git_output
    rdir = receipt_dir(root)
    missing: list[str] = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if not parts:
            continue
        if len(parts) != 4:
            missing.append('MALFORMED_PUSH_REF')
            continue
        m = re.fullmatch(r'refs/tags/v([0-9]+\.[0-9]+\.[0-9]+)', parts[2])
        if not m:
            continue
        version = m.group(1)
        try:
            if re.fullmatch('[0-9a-f]{40,64}', parts[1]) is None or not parts[1].strip('0'):
                raise ValueError('INVALID_TAG_TARGET')
            target = git_output(root, ['rev-parse', parts[1] + '^{commit}']).strip()
            valid = _version_tag_authorized(root, version, target)
        except (OSError, ValueError):
            valid = False
        if not valid:
            missing.append(f'v{version}')
    if not missing:
        return 0
    sys.stderr.write(BLOCK_BANNER.replace('SOURCE-WRITE GATE', 'RELEASE GATE'))
    sys.stderr.write('  Release tag push blocked: no exact version/commit release evidence.\n')
    sys.stderr.write(f"  Tags: {', '.join(missing)}\n")
    sys.stderr.write(f'  Expected receipt in: {rdir.relative_to(root)}/<version>.json\n\n')
    sys.stderr.write('  Run the release through the orchestrator instead:\n')
    sys.stderr.write('    python tools/release.py     # installed projects: python .agents/release.py ; or: make release\n')
    sys.stderr.write('  It runs gates in order and writes the receipt that unlocks the push.\n')
    sys.stderr.write('  Emergency bypass (logged): AIWF_BYPASS=1.\n')
    sys.stderr.write('==================================================================\n')
    return 1


def _version_tag_authorized(root: Path, version: str, target: str) -> bool:
    try:
        before = (root / RELEASE_AUTH_REL).read_bytes()
        value: object = json.loads(before)
    except (OSError, ValueError):
        value = None
        before = b''
    candidate = cast(dict[str, object], value) if isinstance(value, dict) else None
    if isinstance(candidate, dict) and candidate.get('version') == version:
        scope = candidate.get('scope')
        if isinstance(scope, list) and all(isinstance(p, str) for p in cast(list[object], scope)):
            snapshot = git_release_snapshot(root, cast(list[str], scope), target,
                expected_authorization_sha256=hashlib.sha256(before).hexdigest())
            if snapshot is not None and snapshot.version == version:
                return True
    receipt = read_json(receipt_dir(root) / (version + '.json'))
    if not isinstance(receipt, dict) or receipt.get('version') != version:
        return False
    finished = receipt.get('finished_at')
    if not isinstance(finished, str) or parse_iso(finished) is None:
        return False
    repos = receipt.get('repos')
    if not isinstance(repos, list):
        return False
    for value in cast(list[object], repos):
        if isinstance(value, dict):
            repo = cast(dict[str, object], value)
            if repo.get('path') == '.' and repo.get('tag') == 'v' + version and repo.get('sha') == target:
                return True
    return False



def _release_authorization_status(root: Path, staged: list[str] | None = None) -> tuple[bool, str]:
    return release_authorization_status(root, staged)


__all__ = ["_release_authorization_status", "release_authorization_status", "receipt_dir", "RELEASE_AUTH_REL", "cmd_check_release_tags"]
