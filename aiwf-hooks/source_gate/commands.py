"""Path-aware CLI adapters. Release checks are deliberately separate."""
from __future__ import annotations

import argparse
from argparse import Namespace
import os
import sys
import time
from typing import cast
from collections.abc import Sequence
from pathlib import Path

from .capabilities import authorize_paths
from .domain import ActorContext, DecisionReason, PathDecision, RepoPath, SourceOperation
from .git_changes import is_commit_or_history_authorized, change_history_authorized, outgoing_pairs, staged_changes
from .legacy import AUTH_REL, active_workflow_id, is_canonical_blueprint_path, now, read_json, repo_file, repo_relative, sha256_file, source_authorization_status, active_work_item, is_aiwf_project, is_source_file, repo_root
from .ports import BatchDecision, SourceChange
from .release import RELEASE_AUTH_REL, release_authorization_status, cmd_check_release_tags
from .repository import JsonCapabilityRepository
from .policy import gates_enforced

BLOCK_BANNER = '\nAIWF SOURCE-WRITE GATE -- BLOCKED\n'
HELP_TEXT = 'Resume the owning item through AIWF; approve its reviewed Blueprint and enter implementation.\n'


def bypassed() -> bool:
    if not gates_enforced():
        return True
    enabled = os.environ.get('AIWF_BYPASS', '') not in ('', '0', 'false', 'False')
    if enabled:
        sys.stderr.write('[aiwf-gate] AIWF_BYPASS set -- emergency bypass logged.\n')
    return enabled


def check_paths(root: Path, paths: Sequence[str], work_item: str | None = None) -> BatchDecision:
    if not gates_enforced():
        return BatchDecision(True, ())
    repository = JsonCapabilityRepository(root)
    actor = _actor(repository, work_item)
    changes: list[SourceChange] = []
    invalid: list[PathDecision] = []
    for value in paths:
        relative = repo_relative(root, value)
        if relative is None or not is_source_file(root, value):
            continue
        try:
            changes.append(SourceChange(RepoPath(relative, windows=os.name == 'nt'), SourceOperation.MODIFY, None))
        except ValueError:
            invalid.append(PathDecision(False, DecisionReason.SCOPE_INVALID, value, SourceOperation.MODIFY, actor.work_item_id))
    try:
        result = _batch(root, changes, actor)
    except (OSError, ValueError) as exc:
        reason = DecisionReason.CONTEXT_MISMATCH if str(exc) == 'CONTEXT_MISMATCH' else DecisionReason.CAPABILITY_INVALID
        result = BatchDecision(False, tuple(PathDecision(False, reason, c.path.value, c.operation, actor.work_item_id) for c in changes))
    decisions = (*result.decisions, *invalid)
    return BatchDecision(all(d.allowed for d in decisions), decisions)


def _batch(root: Path, changes: Sequence[SourceChange], actor: ActorContext | None = None) -> BatchDecision:
    repository = JsonCapabilityRepository(root)
    actor = actor or _actor(repository)
    source = [c for c in changes if is_source_file(root, c.path.value) or (c.old_path and is_source_file(root, c.old_path.value))]
    if repository.scoped:
        return authorize_paths(source, actor, repository, int(time.time()))
    ok, _ = source_authorization_status(root)
    active = active_workflow_id(root)
    scope: tuple[str, ...] = ()
    if ok and active:
        approval = read_json(root / f'.agents/state/work-items/{active}/approvals.json') or read_json(root / '.agents/state/approvals.json')
        if isinstance(approval, dict) and isinstance(approval.get('blueprint'), dict):
            try:
                _, scope = repository.approved_scope(str(cast(dict[str, object], approval['blueprint']).get('path', '')))
            except (OSError, ValueError):
                pass
    decisions: list[PathDecision] = []
    for change in source:
        for path in [change.path] + ([change.old_path] if change.old_path else []):
            allowed = ok and path.value in scope and (not actor.work_item_id or actor.work_item_id == active)
            decisions.append(PathDecision(allowed, DecisionReason.ALLOW if allowed else DecisionReason.SCOPE_UNOWNED,
                                          path.value, change.operation, active))
    return BatchDecision(all(d.allowed for d in decisions), tuple(decisions))


def _deny(result: BatchDecision) -> int:
    if result.all_allowed:
        return 0
    sys.stderr.write(BLOCK_BANNER)
    for decision in result.decisions:
        if not decision.allowed:
            sys.stderr.write(describe_decision(decision) + '\n')
    sys.stderr.write(HELP_TEXT)
    return 1


def describe_decision(decision: PathDecision) -> str:
    repairs = {'SCOPE_INVALID':'Correct the canonical path and reviewed scope',
               'CONTEXT_MISMATCH':'Resume the owning item/session', 'CAPABILITY_INVALID':'Reissue this item receipt through runtime',
               'CAPABILITY_INACTIVE':'Revalidate eligible work; revoked approval needs owner approval',
               'APPROVAL_MISMATCH':'Repair the bound artifact and reapprove changed content',
               'SNAPSHOT_CHANGED':'Retry the affected item against a stable snapshot',
               'SCOPE_CONFLICT':'Narrow or transfer the shared path through reviewed approval',
               'SCOPE_UNOWNED':'Add this exact path to a reviewed Blueprint and approve changed scope'}
    evidence = f'.agents/state/work-items/{decision.work_item_id}/implementation-entry-receipt.json' if decision.work_item_id else '.agents/state/work-items/'
    return (f'{decision.path}: {decision.reason.value} item={decision.work_item_id} operation={decision.operation.value} '
            f'conflicts={decision.conflicting_work_items} evidence={evidence} repair={repairs.get(decision.reason.value, "Continue")}')


def _actor(repository: JsonCapabilityRepository, item: str | None = None) -> ActorContext:
    return ActorContext(repository.project_id, item or os.environ.get('AIWF_WORK_ITEM_ID') or os.environ.get('AIWF_ACTIVE_WORK_ITEM'),
                        os.environ.get('AIWF_OWNER_ID'), os.environ.get('AIWF_SESSION_ID'))


def cmd_check_git(args: Namespace) -> int:
    root = repo_root()
    if not root or not is_aiwf_project(root) or bypassed():
        return 0
    try:
        changes = staged_changes(root)
        from .release import git_release_snapshot
        paths = [path.value for change in changes for path in [change.path] + ([change.old_path] if change.old_path else [])
                 if is_source_file(root, path.value)]
        if git_release_snapshot(root, paths) is not None:
            return 0
        return _deny(_batch(root, changes))
    except (OSError, ValueError) as exc:
        sys.stderr.write(str(exc) + '\n')
        return 1


def cmd_check_file(args: argparse.Namespace) -> int:
    root = repo_root()
    if not root or not is_aiwf_project(root) or bypassed():
        return 0
    return _deny(check_paths(root, [str(args.path)], getattr(args, 'work_item', None)))


def cmd_check_files(args: argparse.Namespace) -> int:
    root = repo_root()
    if not root or not is_aiwf_project(root) or bypassed():
        return 0
    unauthorized: list[str] = []
    try:
        for line in sys.stdin.read().splitlines():
            fields = line.split('\t', 2)
            if len(fields) == 3:
                local, remote, path = fields
                if is_source_file(root, path) and not is_commit_or_history_authorized(root, path, local, remote):
                    unauthorized.append(path)
            elif line and not check_paths(root, [line]).all_allowed:
                unauthorized.append(line)
    except (OSError, ValueError):
        unauthorized.append('GIT_INSPECTION_FAILED')
    if unauthorized:
        sys.stderr.write('Unauthorized source files in the push: ' + ', '.join(unauthorized) + '\n')
        return 1
    return 0


def cmd_check_outgoing(args: argparse.Namespace) -> int:
    root = repo_root()
    if not root or not is_aiwf_project(root) or bypassed():
        return 0
    try:
        denied: list[str] = []
        for commit, change in outgoing_pairs(root, sys.stdin.read().splitlines()):
            endpoints = [change.path] + ([change.old_path] if change.old_path else [])
            if any(is_source_file(root, path.value) for path in endpoints) and not change_history_authorized(root, commit, change):
                denied.extend(f'{commit}:{path.value}:HISTORY_OWNER_MISMATCH_OR_MISSING' for path in endpoints)
        if denied:
            sys.stderr.write('Unauthorized source files in the push: ' + ', '.join(denied) + '\n')
            return 1
        return 0
    except (OSError, ValueError) as exc:
        sys.stderr.write(str(exc) + '\n')
        return 1


def authorization_status(root: Path) -> tuple[bool, str]:
    if not gates_enforced():
        return True, 'AIWF gates disabled; approval receipts are not required'
    if (root / RELEASE_AUTH_REL).is_file():
        return release_authorization_status(root)
    repository = JsonCapabilityRepository(root)
    if repository.scoped:
        records = repository.load_snapshot(None).records
        return False, f'{len(records)} scoped records; status is not path authorization'
    return source_authorization_status(root)


def cmd_status(args: argparse.Namespace) -> int:
    root = repo_root()
    if not root:
        return 1
    if not gates_enforced():
        print(f'repo: {root}\ngate mode: off\nchecks: SKIPPED\napproval required: False')
        return 0
    repository = JsonCapabilityRepository(root)
    snapshot = repository.load_snapshot(None)
    ok, reason = authorization_status(root)
    print(f'repo: {root}\ndisplay focus: {active_work_item(root)}')
    if repository.scoped:
        print('source mode: scoped; check-file decides permission for an exact path')
    else:
        print(f'authorized: {ok}\nreason: {reason}')
    for record in snapshot.records:
        print(f'{record.work_item_id}: {record.status.value} paths={len(record.scope)} bindings_valid={record.bindings_valid}')
    for item, diagnostic in repository.diagnostics.items():
        print(f'{item}: invalid {diagnostic}')
    return 0


def cmd_authorize(args: argparse.Namespace) -> int:
    from datetime import timedelta
    root = repo_root()
    if not root or JsonCapabilityRepository(root).scoped:
        sys.stderr.write('Scoped mode: source authorization must be issued by the owning workflow.\n')
        return 1
    wi = args.work_item or active_workflow_id(root)
    blueprint = repo_file(root, args.blueprint)
    if not wi or blueprint is None or not is_canonical_blueprint_path(root, blueprint):
        return 1
    value = {'work_item': wi, 'authorized': True, 'blueprint_path': args.blueprint,
             'blueprint_sha256': sha256_file(blueprint), 'approved_by': args.by, 'approved_at': now().isoformat()}
    if args.ttl_hours:
        value['expires_at'] = (now() + timedelta(hours=args.ttl_hours)).isoformat()
    from .repository import atomic_json
    atomic_json(root / AUTH_REL, value)
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    root = repo_root()
    if not root:
        return 1
    item = getattr(args, 'work_item', None)
    if item:
        try:
            JsonCapabilityRepository(root).revoke(item)
        except (OSError, ValueError) as exc:
            sys.stderr.write(str(exc) + '\n')
            return 1
    elif (root / AUTH_REL).is_file():
        (root / AUTH_REL).unlink()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='aiwf_gate')
    sub = parser.add_subparsers(dest='cmd', required=True)
    for name, function in [('check-git', cmd_check_git), ('check-files', cmd_check_files),
                           ('check-outgoing', cmd_check_outgoing), ('check-release-tags', cmd_check_release_tags), ('status', cmd_status)]:
        sub.add_parser(name).set_defaults(fn=function)
    check = sub.add_parser('check-file')
    check.add_argument('path')
    check.add_argument('--work-item')
    check.set_defaults(fn=cmd_check_file)
    auth = sub.add_parser('authorize')
    auth.add_argument('--work-item')
    auth.add_argument('--blueprint', required=True)
    auth.add_argument('--by', default='user')
    auth.add_argument('--ttl-hours', type=float, default=0)
    auth.set_defaults(fn=cmd_authorize)
    revoke = sub.add_parser('revoke')
    revoke.add_argument('--work-item')
    revoke.set_defaults(fn=cmd_revoke)
    return parser


def main(argv: list[str] | None = None) -> int:
    from collections.abc import Callable
    from typing import cast
    args = build_parser().parse_args(argv)
    handler = cast(Callable[[argparse.Namespace], int], args.fn)
    return handler(args)
