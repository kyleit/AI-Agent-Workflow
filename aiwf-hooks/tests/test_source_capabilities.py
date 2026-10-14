from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_gate import ActorContext, IssueRequest, SourceChange, SourceOperation, authorize_paths, issue_capability
from source_gate.domain import RepoPath
from source_gate.repository import JsonCapabilityRepository


def approved_item(root: Path, item: str, scope: tuple[str, ...]) -> IssueRequest:
    root.joinpath('.agents').mkdir(exist_ok=True)
    root.joinpath('.agents/AI_RULES.md').write_text('# rules\n', encoding='utf-8')
    bp = f'docs/features/test/blueprints/{item}_blueprint.md'
    target = root / bp
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f'---\nfeature_id: {item}\n---\n\n## File-By-File Change Matrix\n\n'
                      '| File | Layer | Operation | Code Block IDs |\n|---|---|---|---|\n'
                      + ''.join(f'| `{p}` | application | create | TEST |\n' for p in scope), encoding='utf-8')
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    ap = f'.agents/state/work-items/{item}/approvals.json'
    (root / ap).parent.mkdir(parents=True, exist_ok=True)
    (root / ap).write_text(json.dumps({'blueprint': {'approved': True, 'work_item_id': item,
        'path': bp, 'sha256': digest, 'approved_by': 'owner', 'approved_at': '2026-10-14T00:00:00Z'}}), encoding='utf-8')
    gp = root / f'docs/aiwf-runs/{item}/05-blueprint/code-block-gate.json'
    gp.parent.mkdir(parents=True, exist_ok=True)
    gp.write_text(json.dumps({'decision': 'PASS', 'authority': 'strict-code-block-gate',
                             'blueprint_path': bp, 'blueprint_full_sha256': digest, 'blocking_findings': []}), encoding='utf-8')
    (root / ap).with_name('workflow.json').write_text(json.dumps({'active_workflow': item,
         'active_phase': 'implementation', 'status': 'IN_PROGRESS'}), encoding='utf-8')
    return IssueRequest(JsonCapabilityRepository(root).project_id, item, 'implementation', bp, digest,
                        {bp: digest}, ap, f'BLUEPRINT-APPROVAL-{item}', scope, 'owner', 'session', 1000)


def check(root: Path, path: str, item: str | None = None, now: int = 1001) -> tuple[bool, str]:
    from source_gate.capabilities import authorize_paths as evaluate
    repo = JsonCapabilityRepository(root)
    result = evaluate([SourceChange(RepoPath(path, windows=True), SourceOperation.MODIFY, None)],
                      ActorContext(repo.project_id, item), repo, now)
    return result.all_allowed, result.decisions[0].reason.value


def test_disjoint_items_remain_authorized(tmp_path: Path) -> None:
    for item, scope in [('FEAT-001', ('a.py',)), ('QUICK-002', ('b.py',))]:
        assert issue_capability(tmp_path, approved_item(tmp_path, item, scope)).issued
    pending = tmp_path / '.agents/state/work-items/FIX-003'
    pending.mkdir()
    (pending / 'implementation-entry-receipt.json').write_text('{broken', encoding='utf-8')
    assert check(tmp_path, 'a.py')[0]
    assert check(tmp_path, 'b.py')[0]
    assert check(tmp_path, 'c.py') == (False, 'SCOPE_UNOWNED')
    assert check(tmp_path, 'a.py', 'FIX-003') == (False, 'CAPABILITY_INVALID')


def test_overlap_is_local_and_explicit_identity_never_falls_back(tmp_path: Path) -> None:
    for item, scope in [('FEAT-001', ('shared.py', 'a.py')), ('QUICK-002', ('shared.py', 'b.py'))]:
        assert issue_capability(tmp_path, approved_item(tmp_path, item, scope)).issued
    assert check(tmp_path, 'shared.py') == (False, 'SCOPE_CONFLICT')
    assert check(tmp_path, 'a.py')[0] and check(tmp_path, 'b.py')[0]
    assert check(tmp_path, 'b.py', 'FEAT-001') == (False, 'SCOPE_UNOWNED')
    assert check(tmp_path, 'A.py')[0]


def test_receipt_tampering_and_expiry_fail_closed(tmp_path: Path) -> None:
    request = approved_item(tmp_path, 'FEAT-001', ('a.py',))
    result = issue_capability(tmp_path, request)
    assert result.issued
    assert check(tmp_path, 'a.py', 'FEAT-001', now=87401) == (False, 'CAPABILITY_INACTIVE')
    receipt = tmp_path / result.receipt_path
    data = json.loads(receipt.read_text())
    data['write_scope'] = ['evil.py']
    receipt.write_text(json.dumps(data), encoding='utf-8')
    assert not check(tmp_path, 'evil.py')[0]


def test_changed_approval_and_artifact_deny_only_affected_item(tmp_path: Path) -> None:
    a = approved_item(tmp_path, 'FEAT-001', ('a.py',))
    b = approved_item(tmp_path, 'QUICK-002', ('b.py',))
    assert issue_capability(tmp_path, a).issued and issue_capability(tmp_path, b).issued
    (tmp_path / a.blueprint_path).write_text('changed', encoding='utf-8')
    assert not check(tmp_path, 'a.py')[0]
    assert check(tmp_path, 'b.py')[0]
    assert not issue_capability(tmp_path, a).issued


@pytest.mark.parametrize('path', ['../bad.py', '/bad.py', 'C:bad.py', '//host/file.py', 'src/*.py', 'src/', 'src/./x.py'])
def test_invalid_scope_is_rejected(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match='SCOPE_INVALID'):
        RepoPath(path)


def test_renewal_does_not_require_another_approval(tmp_path: Path) -> None:
    from dataclasses import replace
    request = approved_item(tmp_path, 'FEAT-001', ('a.py',))
    first = issue_capability(tmp_path, request)
    second = issue_capability(tmp_path, replace(request, now=2000))
    assert first.issued and second.issued
    assert second.receipt['revision'] == 2
    assert second.receipt['capability_id'] == first.receipt['capability_id']


def test_directory_and_escaping_junction_are_rejected(tmp_path: Path) -> None:
    import os
    import subprocess
    (tmp_path / 'src').mkdir()
    assert not issue_capability(tmp_path, approved_item(tmp_path, 'FEAT-001', ('src',))).issued
    outside = tmp_path.parent / (tmp_path.name + '-outside')
    outside.mkdir()
    link = tmp_path / 'escape'
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], stdin=subprocess.DEVNULL, check=True, capture_output=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    assert not issue_capability(tmp_path, approved_item(tmp_path, 'FEAT-002', ('escape/app.py',))).issued


def test_rename_requires_same_owner_and_checks_both_endpoints(tmp_path: Path) -> None:
    for item, scope in [('FEAT-001', ('a.py',)), ('QUICK-002', ('b.py',))]:
        assert issue_capability(tmp_path, approved_item(tmp_path, item, scope)).issued
    repo = JsonCapabilityRepository(tmp_path)
    actor = ActorContext(repo.project_id)
    from source_gate.capabilities import authorize_paths as evaluate
    result = evaluate([SourceChange(RepoPath('b.py'), SourceOperation.RENAME, RepoPath('a.py'))], actor, repo, 1001)
    assert not result.all_allowed


def test_facade_runs_actual_repository(tmp_path: Path) -> None:
    import time
    from dataclasses import replace
    request = approved_item(tmp_path, 'FEAT-001', ('a.py',))
    assert issue_capability(tmp_path, replace(request, now=int(time.time()))).issued
    result = authorize_paths(tmp_path, [SourceChange(RepoPath('a.py'), SourceOperation.MODIFY, None)],
                             ActorContext(request.project_id))
    assert result.all_allowed


def test_windows_aliases_cannot_create_independent_claims(tmp_path: Path) -> None:
    repo = JsonCapabilityRepository(tmp_path)
    repo.windows = True
    for path in ('app.py.', 'app.py ', 'CON.py', 'src./app.py', 'NUL/app.py'):
        assert not repo.contains(RepoPath(path, windows=True))


def test_blueprint_identity_is_exact_not_substring(tmp_path: Path) -> None:
    request = approved_item(tmp_path, 'FEAT-010', ('app.py',))
    blueprint = tmp_path / request.blueprint_path
    blueprint.write_text(blueprint.read_text().replace('feature_id: FEAT-010', 'feature_id: FEAT-01'), encoding='utf-8')
    repo = JsonCapabilityRepository(tmp_path)
    with pytest.raises(ValueError, match='APPROVAL_MISMATCH'):
        repo.approved_scope(request.blueprint_path)


def test_revoke_and_renew_use_one_lock(tmp_path: Path) -> None:
    repo = JsonCapabilityRepository(tmp_path)
    request = approved_item(tmp_path, 'FEAT-001', ('app.py',))
    result = repo.publish(request)
    assert result.issued
    lock = (tmp_path / result.receipt_path).with_suffix('.lock')
    lock.write_text('occupied', encoding='utf-8')
    with pytest.raises(FileExistsError):
        repo.revoke('FEAT-001')
    assert not repo.publish(request).issued
    lock.unlink()
    repo.revoke('FEAT-001')
    assert repo.publish(request).reason == 'CAPABILITY_INACTIVE'
    assert check(tmp_path, 'app.py', 'FEAT-001') == (False, 'CAPABILITY_INACTIVE')


def test_snapshot_rechecks_approval_bytes(tmp_path: Path) -> None:
    from typing import override
    from source_gate.repository import atomic_json, read_json
    request = approved_item(tmp_path, 'FEAT-001', ('app.py',))
    assert issue_capability(tmp_path, request).issued
    class ChangingRepository(JsonCapabilityRepository):
        @override
        def _approval(self, request: IssueRequest, bind: bool = False) -> dict[str, object]:
            result = super()._approval(request, bind)
            target = self.path(request.approval_path)
            data = read_json(target)
            data['concurrent_revision'] = int(str(data.get('concurrent_revision', 0))) + 1
            atomic_json(target, data)
            return result
    from source_gate.capabilities import authorize_paths as evaluate
    repository = ChangingRepository(tmp_path)
    result = evaluate([SourceChange(RepoPath('app.py'), SourceOperation.MODIFY, None)],
                      ActorContext(repository.project_id, 'FEAT-001'), repository, 1001)
    assert result.decisions[0].reason.value == 'SNAPSHOT_CHANGED'
