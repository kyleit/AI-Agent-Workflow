from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from workflow_runtime.infrastructure.session.state_store import AtomicFileStateStore, RevisionConflictError, get_state_store, reset_state_store


def test_store_scope_is_fixed(tmp_path: Path) -> None:
    root = str(tmp_path / 'state')
    with pytest.MonkeyPatch.context() as context:
        context.setenv('AIWF_WORK_ITEM_ID', 'FEAT-001')
        a = AtomicFileStateStore(root)
        context.setenv('AIWF_WORK_ITEM_ID', 'QUICK-002')
        b = AtomicFileStateStore(root)
    a.set('approvals', {'item': 'A'})
    b.set('approvals', {'item': 'B'})
    a.set('workflow', {'active_workflow': 'FEAT-001'})
    b.set('workflow', {'active_workflow': 'QUICK-002'})
    assert a.get('approvals')['item'] == 'A'
    assert b.get('approvals')['item'] == 'B'
    assert not (Path(root) / 'workflow.json').exists()


def test_factory_is_namespaced_by_root_and_item(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state_store()
    monkeypatch.setenv('AIWF_STATE_ROOT', str(tmp_path / 'a'))
    monkeypatch.setenv('AIWF_WORK_ITEM_ID', 'FEAT-001')
    a = get_state_store()
    a.set('tasks', {'owner': 'a'})
    monkeypatch.setenv('AIWF_WORK_ITEM_ID', 'FIX-002')
    b = get_state_store()
    assert not b.get('tasks')
    b.set('tasks', {'owner': 'b'})
    monkeypatch.setenv('AIWF_WORK_ITEM_ID', 'FEAT-001')
    assert get_state_store().get('tasks')['owner'] == 'a'
    monkeypatch.setenv('AIWF_STATE_ROOT', str(tmp_path / 'b'))
    assert not get_state_store().get('tasks')
    reset_state_store()


def test_cas_reads_actual_disk_not_stale_cache(tmp_path: Path) -> None:
    a = AtomicFileStateStore(str(tmp_path), 'FEAT-001')
    b = AtomicFileStateStore(str(tmp_path), 'FEAT-001')
    a.get('tasks')
    b.set('tasks', {'b': True}, expected_revision=0)
    with pytest.raises(RevisionConflictError):
        a.set('tasks', {'a': True}, expected_revision=0)
    assert a.get('tasks')['b'] is True


def test_explicit_identity_is_validated_before_path_creation(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='CONTEXT_MISMATCH'):
        AtomicFileStateStore(str(tmp_path), '../../escape')


def test_process_race_has_one_winner(tmp_path: Path) -> None:
    code = 'from workflow_runtime.infrastructure.session.state_store import AtomicFileStateStore; import sys; s=AtomicFileStateStore(sys.argv[1],sys.argv[2]); s.set("tasks",{"ok":True},expected_revision=0)'
    env = dict(os.environ)
    env.pop('PYTEST_CURRENT_TEST', None)
    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1])
    children = [subprocess.Popen([sys.executable, '-c', code, str(tmp_path), 'FEAT-001'],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) for _ in range(2)]
    for child in children:
        child.communicate(timeout=30)
    assert sorted(p.returncode for p in children) == [0, 1]
    data = json.loads((tmp_path / 'work-items/FEAT-001/tasks.json').read_text())
    assert data['_metadata']['revision'] == 1


def test_actual_implementation_entry_and_wrong_item(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from argparse import Namespace
    hooks = Path(__file__).resolve().parents[3] / 'tools/aiwf-hooks/tests'
    sys.path.insert(0, str(hooks))
    from test_source_capabilities import approved_item
    from workflow_runtime.presentation.cli.commands._impl.project_manager import do_implement_action
    request = approved_item(tmp_path, 'FEAT-001', ('app.py',))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('AIWF_STATE_ROOT', str(tmp_path / '.agents/state'))
    monkeypatch.setenv('AIWF_WORK_ITEM_ID', 'FEAT-001')
    wrong = Namespace(action=None, blueprint=request.blueprint_path, dry_run=False, work_item='QUICK-002')
    assert do_implement_action(wrong) == 3
    assert not (tmp_path / '.agents/state/work-items/QUICK-002').exists()
    correct = Namespace(action=None, blueprint=request.blueprint_path, dry_run=False, work_item='FEAT-001')
    assert do_implement_action(correct) == 0
    receipt = json.loads((tmp_path / '.agents/state/work-items/FEAT-001/implementation-entry-receipt.json').read_text())
    assert receipt['implementation_phase'] == 'implementation'
    assert receipt['write_scope'] == ['app.py']


def test_runtime_renewal_rejects_changed_scope_and_revoked_approval(tmp_path: Path) -> None:
    from dataclasses import replace
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/aiwf-hooks/tests'))
    from test_source_capabilities import approved_item
    from workflow_runtime.infrastructure.execution.source_capability_adapter import GateSourceCapabilityAdapter
    prepared = approved_item(tmp_path, 'FEAT-001', ('a.py',))
    adapter = GateSourceCapabilityAdapter(tmp_path)
    request = adapter.request(prepared.blueprint_path, 'FEAT-001', 'owner', 'session', 1000)
    assert adapter.issue(request).issued
    assert adapter.issue(replace(request, now=2000)).issued
    assert not adapter.issue(replace(request, scope=('b.py',))).issued
    path = tmp_path / prepared.approval_path
    data = json.loads(path.read_text())
    data['blueprint']['approved'] = False
    path.write_text(json.dumps(data), encoding='utf-8')
    assert not adapter.issue(request).issued
