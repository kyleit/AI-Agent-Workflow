from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

from test_source_capabilities import approved_item
from source_gate import issue_capability
from source_gate.repository import JsonCapabilityRepository

HOOKS = Path(__file__).resolve().parents[1]


def invoke(root: Path, command: str, payload: str = '', *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    for key in ('AIWF_WORK_ITEM_ID', 'AIWF_ACTIVE_WORK_ITEM', 'AIWF_BYPASS'):
        env.pop(key, None)
    result = subprocess.run([sys.executable, str(HOOKS / 'aiwf_gate.py'), command, *args],
                            cwd=root, input=payload, capture_output=True, text=True, env=env)
    assert 'Traceback (most recent call last)' not in result.stderr, result.stderr
    return result


def ready(root: Path, item: str, scope: tuple[str, ...]) -> None:
    assert issue_capability(root, replace(approved_item(root, item, scope), now=int(time.time()))).issued


def test_batch_checks_all_paths(tmp_path: Path) -> None:
    ready(tmp_path, 'FEAT-001', ('a.py',))
    ready(tmp_path, 'QUICK-002', ('b.py',))
    guard = HOOKS / 'claude_source_write_guard.py'
    env = dict(os.environ)
    for key in ('AIWF_WORK_ITEM_ID', 'AIWF_ACTIVE_WORK_ITEM', 'AIWF_BYPASS'):
        env.pop(key, None)
    def run(paths: list[str]) -> subprocess.CompletedProcess[str]:
        payload = {'cwd': str(tmp_path), 'tool_name': 'MultiEdit',
                   'tool_input': {'edits': [{'file_path': p} for p in paths]}}
        return subprocess.run([sys.executable, str(guard)], input=json.dumps(payload),
                              cwd=tmp_path, capture_output=True, text=True, env=env)
    assert run(['a.py', 'b.py']).returncode == 0
    denied = run(['a.py', 'b.py', 'unowned.py'])
    assert denied.returncode == 2 and 'unowned.py' in denied.stderr
    (tmp_path / '.agents/state/release').mkdir()
    (tmp_path / '.agents/state/release/authorization.json').write_text('{}', encoding='utf-8')
    assert run(['a.py']).returncode == 0


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', *args], cwd=root, stdin=subprocess.DEVNULL,
                          check=True, capture_output=True, text=True).stdout.strip()


def test_git_checks_delete_rename_and_space_names(tmp_path: Path) -> None:
    from source_gate.git_changes import staged_changes
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'AIWF test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    for name in ('delete.py', 'old name.py'):
        (tmp_path / name).write_text(f'print({name!r})\n', encoding='utf-8')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'initial')
    git(tmp_path, 'rm', 'delete.py')
    git(tmp_path, 'mv', 'old name.py', 'new name.py')
    changes = staged_changes(tmp_path)
    assert any(c.path.value == 'delete.py' and c.operation.value == 'delete' for c in changes)
    assert any(c.old_path and c.old_path.value == 'old name.py' and c.path.value == 'new name.py' for c in changes)
    ready(tmp_path, 'FEAT-001', ('new name.py',))
    blocked = invoke(tmp_path, 'check-git')
    assert blocked.returncode == 1
    assert 'delete.py' in blocked.stderr and 'old name.py' in blocked.stderr


def test_each_outgoing_commit_needs_its_own_evidence(tmp_path: Path) -> None:
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'AIWF test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    (tmp_path / '.agents').mkdir()
    (tmp_path / '.agents/AI_RULES.md').write_text('# rules', encoding='utf-8')
    (tmp_path / 'a.py').write_text('print(0)\n', encoding='utf-8')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    commits: list[str] = []
    for n in (1, 2):
        (tmp_path / 'a.py').write_text(f'print({n})\n', encoding='utf-8')
        git(tmp_path, 'add', 'a.py')
        git(tmp_path, 'commit', '-qm', f'change {n}')
        commits.append(git(tmp_path, 'rev-parse', 'HEAD'))
    audit = tmp_path / '.agents/state/audit'
    audit.mkdir(parents=True)
    (audit / 'receipt.json').write_text(json.dumps({'commit_sha': commits[0], 'work_item_id': 'FEAT-001',
                                      'authorized': True, 'paths': ['a.py']}), encoding='utf-8')
    refs = f'refs/heads/main {commits[1]} refs/heads/main {base}\n'
    result = invoke(tmp_path, 'check-outgoing', refs)
    assert result.returncode == 1 and commits[1] in result.stderr


def test_git_failure_is_not_empty_success(tmp_path: Path) -> None:
    ready(tmp_path, 'FEAT-001', ('a.py',))
    assert invoke(tmp_path, 'check-git').returncode == 1
    assert JsonCapabilityRepository(tmp_path).scoped


def test_escape_and_subdirectory_cwd_do_not_bypass_guard(tmp_path: Path) -> None:
    ready(tmp_path, 'FEAT-001', ('approved.py',))
    sub = tmp_path / 'src'
    sub.mkdir()
    outside = tmp_path.parent / (tmp_path.name + '-external')
    outside.mkdir()
    link = tmp_path / 'escape'
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], stdin=subprocess.DEVNULL, check=True, capture_output=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    guard = HOOKS / 'claude_source_write_guard.py'
    for cwd, target in [(tmp_path, 'escape/app.py'), (sub, str(tmp_path / 'unowned.py'))]:
        payload = {'cwd': str(cwd), 'tool_name': 'Write', 'tool_input': {'file_path': target}}
        result = subprocess.run([sys.executable, str(guard)], cwd=tmp_path, input=json.dumps(payload),
                                capture_output=True, text=True, env=environment_without_identity())
        assert result.returncode == 2, result.stderr


def environment_without_identity() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in {'AIWF_WORK_ITEM_ID','AIWF_ACTIVE_WORK_ITEM','AIWF_BYPASS','AIWF_OWNER_ID','AIWF_SESSION_ID'}}


def test_git_checks_owner_and_session(tmp_path: Path) -> None:
    git(tmp_path, 'init', '-q')
    ready(tmp_path, 'FEAT-001', ('a.py',))
    (tmp_path / 'a.py').write_text('print(1)', encoding='utf-8')
    git(tmp_path, 'add', 'a.py')
    env = environment_without_identity()
    env.update({'AIWF_WORK_ITEM_ID':'FEAT-001','AIWF_SESSION_ID':'wrong-session'})
    result = subprocess.run([sys.executable, str(HOOKS / 'aiwf_gate.py'), 'check-git'], cwd=tmp_path,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env)
    assert result.returncode == 1 and 'CONTEXT_MISMATCH' in result.stderr


def test_scoped_history_rejects_generic_or_revoked_records(tmp_path: Path) -> None:
    from source_gate.git_changes import history_authorizes
    from source_gate.repository import atomic_json, canonical_hash
    ready(tmp_path, 'FEAT-001', ('a.py',))
    receipt: dict[str, object] = {'commit_sha':'a'*40, 'work_item_id':'FEAT-001', 'authorized':True, 'paths':['a.py']}
    path = tmp_path / '.agents/state/audit/commit.json'
    atomic_json(path, receipt)
    assert not history_authorizes(tmp_path, 'a'*40, 'a.py')
    receipt.update({'schema_version':'aiwf.git-authorization/1','operation':'commit','status':'AUTHORIZED',
                    'project_id':JsonCapabilityRepository(tmp_path).project_id})
    receipt['content_hash'] = canonical_hash(receipt)
    atomic_json(path, receipt)
    assert history_authorizes(tmp_path, 'a'*40, 'a.py')
    receipt['status'] = 'REVOKED'
    receipt.pop('content_hash')
    receipt['content_hash'] = canonical_hash(receipt)
    atomic_json(path, receipt)
    assert not history_authorizes(tmp_path, 'a'*40, 'a.py')


def historical_receipt(root: Path, name: str, commit: str, item: str, paths: list[str]) -> None:
    from source_gate.repository import atomic_json, canonical_hash
    record: dict[str, object] = {'schema_version':'aiwf.git-authorization/1', 'project_id':JsonCapabilityRepository(root).project_id,
        'operation':'commit','status':'AUTHORIZED','authorized':True,'commit_sha':commit,'work_item_id':item,'paths':paths}
    record['content_hash'] = canonical_hash(record)
    atomic_json(root / ('.agents/state/audit/' + name + '.json'), record)


def history_fixture(root: Path) -> None:
    git(root, 'init', '-q')
    git(root, 'config', 'user.name', 'AIWF fixture')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    (root / '.agents/state').mkdir(parents=True)
    (root / '.agents/AI_RULES.md').write_text('# rules', encoding='utf-8')
    (root / '.agents/state/source-capability-mode.json').write_text('{"activated":true}', encoding='utf-8')


def test_outgoing_rename_requires_same_historical_item(tmp_path: Path) -> None:
    history_fixture(tmp_path)
    (tmp_path / 'old.py').write_text('print(1)', encoding='utf-8')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    git(tmp_path, 'mv', 'old.py', 'new.py')
    git(tmp_path, 'commit', '-qm', 'rename')
    head = git(tmp_path, 'rev-parse', 'HEAD')
    historical_receipt(tmp_path, 'old', head, 'FEAT-001', ['old.py'])
    historical_receipt(tmp_path, 'new', head, 'QUICK-002', ['new.py'])
    refs = f'refs/heads/main {head} refs/heads/main {base}\n'
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 1
    historical_receipt(tmp_path, 'new', head, 'FEAT-001', ['new.py'])
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 0


def test_new_branch_merge_and_utf8_paths(tmp_path: Path) -> None:
    history_fixture(tmp_path)
    (tmp_path / 'base.md').write_text('# base', encoding='utf-8')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    branch = git(tmp_path, 'branch', '--show-current')
    name = 'caf\u00e9 name.py'
    (tmp_path / name).write_text('print(1)', encoding='utf-8')
    git(tmp_path, 'add', name)
    git(tmp_path, 'commit', '-qm', 'utf8 source')
    head = git(tmp_path, 'rev-parse', 'HEAD')
    historical_receipt(tmp_path, 'utf8', head, 'FEAT-001', [name])
    refs = f'refs/heads/{branch} {head} refs/heads/{branch} {"0" * 40}\n'
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 0


    git(tmp_path, 'checkout', '-qb', 'side', base)
    (tmp_path / 'other.py').write_text('print(2)', encoding='utf-8')
    git(tmp_path, 'add', 'other.py')
    git(tmp_path, 'commit', '-qm', 'side source')
    side = git(tmp_path, 'rev-parse', 'HEAD')
    historical_receipt(tmp_path, 'side', side, 'QUICK-002', ['other.py'])
    git(tmp_path, 'checkout', '-q', branch)
    git(tmp_path, 'merge', '--no-ff', 'side', '-m', 'merge fixture')
    merge = git(tmp_path, 'rev-parse', 'HEAD')
    refs = f'refs/heads/{branch} {merge} refs/heads/{branch} {base}\n'
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 1
    historical_receipt(tmp_path, 'merge-utf8', merge, 'FEAT-001', [name])
    historical_receipt(tmp_path, 'merge-side', merge, 'QUICK-002', ['other.py'])
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 0


def test_real_release_snapshot_can_publish_without_granting_source_edits(tmp_path: Path) -> None:
    import hashlib
    import shutil
    from datetime import datetime, timedelta, timezone
    from source_gate.legacy import scope_digest
    from source_gate.repository import atomic_json

    history_fixture(tmp_path)
    shutil.copytree(HOOKS, tmp_path / 'tools/aiwf-hooks', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    (tmp_path / 'base.md').write_text('# base', encoding='utf-8')
    (tmp_path / 'pre_framework.py').write_text('print(0)\n', encoding='utf-8')
    git(tmp_path, 'add', 'base.md', 'pre_framework.py')
    git(tmp_path, 'commit', '-qm', 'existing published project baseline')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    remote = tmp_path / 'isolated-remote.git'
    subprocess.run(['git', 'init', '--bare', '-q', str(remote)], stdin=subprocess.DEVNULL, check=True, capture_output=True)
    git(tmp_path, 'remote', 'add', 'origin', str(remote))
    git(tmp_path, 'push', 'origin', 'HEAD:refs/heads/main')
    git(tmp_path, 'config', 'core.hooksPath', str(HOOKS.parent / 'githooks'))
    ready(tmp_path, 'FEAT-001', ('editable.py',))
    atomic_json(tmp_path / '.agents/state/workflow.json', {'active_workflow': 'FEAT-001', 'active_phase': 'implementation'})
    source = tmp_path / 'release_only.py'
    source.write_text('print(1)\n', encoding='utf-8')
    git(tmp_path, 'add', 'release_only.py')
    blueprint = 'docs/features/test/blueprints/FEAT-001_blueprint.md'
    for name in ('debug', 'verify'):
        (tmp_path / (name + '.md')).write_text('---\nstatus: PASS\n---\n', encoding='utf-8')
    version = '9.0.0'
    atomic_json(tmp_path / '.agents/state/release' / (version + '.json'), {'version': version})
    auth: dict[str, object] = {'authorized': True, 'operation': 'release', 'release_mode': 'workflow',
        'work_item': 'FEAT-001', 'version': version, 'blueprint_path': blueprint,
        'blueprint_sha256': hashlib.sha256((tmp_path / blueprint).read_bytes()).hexdigest(),
        'debug_path': 'debug.md', 'verification_path': 'verify.md', 'scope': ['release_only.py'],
        'scope_sha256': scope_digest(tmp_path, ['release_only.py']),
        'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()}
    authorization = tmp_path / '.agents/state/release/authorization.json'
    atomic_json(authorization, auth)
    # Publication permission is separate from edit permission, even for the same path.
    assert invoke(tmp_path, 'check-file', '', 'release_only.py').returncode == 1
    assert invoke(tmp_path, 'check-git').returncode == 0
    expires = auth['expires_at']
    auth['expires_at'] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    atomic_json(authorization, auth)
    assert invoke(tmp_path, 'check-git').returncode == 1
    auth['expires_at'] = expires
    atomic_json(authorization, auth)
    # A valid worktree approval cannot authorize different staged blob contents.
    source.write_text('print(2)\n', encoding='utf-8')
    auth['scope_sha256'] = scope_digest(tmp_path, ['release_only.py'])
    atomic_json(authorization, auth)
    assert invoke(tmp_path, 'check-git').returncode == 1
    git(tmp_path, 'add', 'release_only.py')
    git(tmp_path, 'commit', '-qm', 'approved release snapshot')
    head = git(tmp_path, 'rev-parse', 'HEAD')
    refs = f'refs/heads/main {head} refs/heads/main {base}\n'
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 1  # Missing reviewed version tag.
    git(tmp_path, 'tag', 'v' + version, base)
    wrong_tag = f'refs/tags/v{version} {base} refs/tags/v{version} {"0" * 40}\n'
    assert invoke(tmp_path, 'check-release-tags', wrong_tag).returncode == 1
    git(tmp_path, 'tag', '-f', 'v' + version, head)
    from source_gate.release import git_release_snapshot
    captured_consent = hashlib.sha256(authorization.read_bytes()).hexdigest()
    replacement = dict(auth)
    replacement['version'] = '10.0.0'
    atomic_json(tmp_path / '.agents/state/release/10.0.0.json', {'version': '10.0.0'})
    git(tmp_path, 'tag', 'v10.0.0', head)
    atomic_json(authorization, replacement)
    control = git_release_snapshot(tmp_path, ['release_only.py'], head)
    assert control is not None and control.version == '10.0.0'
    assert git_release_snapshot(tmp_path, ['release_only.py'], head,
                               expected_authorization_sha256=captured_consent) is None
    replacement['version'] = version
    replacement['scope'] = ['release_only.py', 'base.md']
    replacement['scope_sha256'] = scope_digest(tmp_path, ['release_only.py', 'base.md'])
    atomic_json(authorization, replacement)
    assert git_release_snapshot(tmp_path, ['release_only.py'], head) is not None
    assert git_release_snapshot(tmp_path, ['release_only.py'], head,
                               expected_authorization_sha256=captured_consent) is None
    atomic_json(authorization, auth)
    git(tmp_path, 'push', 'origin', 'HEAD:refs/heads/main')
    # Consuming live release consent must leave exact commit/path audit evidence.
    authorization.unlink()
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 0
    assert invoke(tmp_path, 'check-file', '', 'release_only.py').returncode == 1
    denied = subprocess.run(['git', 'push', 'origin', 'v' + version], cwd=tmp_path,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert denied.returncode == 1  # A file's existence is not completed release evidence.
    atomic_json(authorization, auth)
    git(tmp_path, 'push', 'origin', 'v' + version)
    atomic_json(tmp_path / '.agents/state/release' / (version + '.json'), {
        'version': version, 'finished_at': datetime.now(timezone.utc).isoformat(),
        'repos': [{'path': '.', 'tag': 'v' + version, 'sha': head}]})
    authorization.unlink()
    correct_tag = f'refs/tags/v{version} {head} refs/tags/v{version} {"0" * 40}\n'
    assert invoke(tmp_path, 'check-release-tags', correct_tag).returncode == 0
    assert invoke(tmp_path, 'check-release-tags', wrong_tag).returncode == 1
    atomic_json(tmp_path / '.agents/state/release/8.0.0.json', {'version': '8.0.0'})
    wrong_version = f'refs/tags/v8.0.0 {head} refs/tags/v8.0.0 {"0" * 40}\n'
    assert invoke(tmp_path, 'check-release-tags', wrong_version).returncode == 1
    from source_gate.repository import canonical_hash, read_json
    audit = next((tmp_path / '.agents/state/audit').glob('release-*.json'))
    original = read_json(audit)
    changed = dict(original)
    changed['blob_oids'] = {'release_only.py': '0' * 40}
    changed.pop('content_hash')
    changed['content_hash'] = canonical_hash(changed)
    atomic_json(audit, changed)
    assert invoke(tmp_path, 'check-outgoing', refs).returncode == 1
    atomic_json(audit, original)
    assert git(tmp_path, 'rev-parse', 'HEAD') == subprocess.run(
        ['git', '--git-dir', str(remote), 'rev-parse', 'refs/heads/main'], stdin=subprocess.DEVNULL, check=True,
        capture_output=True, text=True).stdout.strip()


def test_new_branch_only_excludes_the_named_destination_history(tmp_path: Path) -> None:
    history_fixture(tmp_path)
    (tmp_path / 'base.md').write_text('# base', encoding='utf-8')
    git(tmp_path, 'add', 'base.md')
    git(tmp_path, 'commit', '-qm', 'base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    (tmp_path / 'unapproved.py').write_text('print(1)', encoding='utf-8')
    git(tmp_path, 'add', 'unapproved.py')
    git(tmp_path, 'commit', '-qm', 'not authorized on destination')
    head = git(tmp_path, 'rev-parse', 'HEAD')
    git(tmp_path, 'remote', 'add', 'origin', str(tmp_path / 'origin.git'))
    git(tmp_path, 'remote', 'add', 'other', str(tmp_path / 'other.git'))
    git(tmp_path, 'update-ref', 'refs/remotes/origin/main', base)
    git(tmp_path, 'update-ref', 'refs/remotes/other/main', head)
    env = environment_without_identity()
    env['AIWF_PUSH_REMOTE'] = 'origin'
    refs = f'refs/heads/new {head} refs/heads/new {"0" * 40}\n'
    result = subprocess.run([sys.executable, str(HOOKS / 'aiwf_gate.py'), 'check-outgoing'], cwd=tmp_path,
                            input=refs, capture_output=True, text=True, env=env)
    assert result.returncode == 1 and 'unapproved.py' in result.stderr


def test_fetch_history_cannot_authorize_a_different_pushurl(tmp_path: Path) -> None:
    import shutil
    history_fixture(tmp_path)
    for name in ('fetch.git', 'push.git'):
        subprocess.run(['git', 'init', '--bare', '-q', str(tmp_path / name)], stdin=subprocess.DEVNULL,
                       check=True, capture_output=True)
    (tmp_path / 'base.md').write_text('# base', encoding='utf-8')
    git(tmp_path, 'add', 'base.md')
    git(tmp_path, 'commit', '-qm', 'base')
    git(tmp_path, 'remote', 'add', 'origin', str(tmp_path / 'fetch.git'))
    git(tmp_path, 'remote', 'add', 'destination', str(tmp_path / 'push.git'))
    git(tmp_path, 'push', 'origin', 'HEAD:refs/heads/main')
    git(tmp_path, 'push', 'destination', 'HEAD:refs/heads/main')
    (tmp_path / 'unapproved.py').write_text('print(1)', encoding='utf-8')
    git(tmp_path, 'add', 'unapproved.py')
    git(tmp_path, 'commit', '-qm', 'published only on fetch origin')
    git(tmp_path, 'push', 'origin', 'HEAD:refs/heads/main')
    git(tmp_path, 'config', 'remote.origin.pushurl', str(tmp_path / 'push.git'))
    shutil.copytree(HOOKS, tmp_path / 'tools/aiwf-hooks', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    git(tmp_path, 'config', 'core.hooksPath', str(HOOKS.parent / 'githooks'))
    result = subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/new'], cwd=tmp_path,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert result.returncode == 1 and 'unapproved.py' in result.stderr
