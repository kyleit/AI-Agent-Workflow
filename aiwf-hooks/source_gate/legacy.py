from __future__ import annotations
import datetime as _dt
import hashlib
import json
import os
import re
from typing import cast
from pathlib import Path
from .domain import ActorContext, CapabilitySnapshot, DecisionReason, PathDecision, RepoPath, SourceOperation, evaluate_path
def validate_legacy_claim(snapshot: CapabilitySnapshot, path: RepoPath) -> PathDecision:
    if len(snapshot.records) != 1:
        return PathDecision(False, DecisionReason.CAPABILITY_INVALID, path.value, SourceOperation.MODIFY, None)
    record = snapshot.records[0]
    return evaluate_path(path, SourceOperation.MODIFY, ActorContext(record.project_id, record.work_item_id), snapshot, int(now().timestamp()))
SOURCE_EXTS = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.go', '.rs', '.rb', '.php', '.java', '.c', '.cc', '.cpp', '.h', '.hpp', '.cs', '.css', '.scss', '.sass', '.html', '.htm', '.vue', '.svelte', '.sql', '.ps1', '.psm1', '.sh', '.bash', '.zsh', '.kt', '.swift'}
EXCLUDED_PREFIXES = ('.agents/', 'public_export/', 'docs/', '.git/', '.claude/', 'skills/strict-code-block-gate/', 'tools/githooks/', 'tools/aiwf-hooks/', 'node_modules/', '__pycache__/', '.vscode/', 'scratch/', 'tmp/', 'test-results/', 'screenshots/', 'artifacts/', 'interactive-docs/', 'desktop/')
AUTH_REL = '.agents/state/source-write-authorization.json'
WORKFLOW_REL = '.agents/state/workflow.json'
APPROVALS_REL = '.agents/state/approvals.json'
CODE_BLOCK_GATE_STATE_REL = '.agents/state/code-block-gate.json'
AIWF_MARKER_REL = '.agents/AI_RULES.md'
IMPLEMENTATION_PHASES = {'implementation', 'implementing', 'implement', 'debug', 'debugging', 'verify', 'verification', 'verifying', 'release', 'releasing'}
def repo_root(start: Path | None=None) -> Path | None:
    probe = (start or Path.cwd()).resolve()
    for parent in (probe, *probe.parents):
        if is_aiwf_project(parent) or (parent / '.git').exists():
            return parent
    return probe
def is_aiwf_project(root: Path) -> bool:
    return (root / AIWF_MARKER_REL).exists() or (root / 'AI_RULES.md').exists() or (root / '.agents' / 'project.config.json').exists()
def rel_posix(root: Path, path: str) -> str:
    p = Path(path)
    try:
        rel = p.resolve().relative_to(root.resolve())
    except Exception:
        rel = Path(str(path).replace('\\', '/'))
    return rel.as_posix()
def repo_relative(root: Path, path: str) -> str | None:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        lexical = Path(os.path.abspath(candidate)).relative_to(root.resolve()).as_posix()
    except ValueError:
        lexical = None
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError):
        return lexical
def is_source_file(root: Path, path: str) -> bool:
    rel = repo_relative(root, path)
    if rel is None:
        return False
    if any((rel == '' or rel.startswith(pref) for pref in EXCLUDED_PREFIXES)):
        return False
    if rel.lower().endswith('.md'):
        return False
    return Path(rel.rstrip(' .') if os.name == 'nt' else rel).suffix.lower() in SOURCE_EXTS
def read_json(path: Path) -> dict[str, object] | None:
    try:
        value: object = json.loads(path.read_text(encoding='utf-8-sig'))
        return cast(dict[str, object], value) if isinstance(value, dict) else None
    except Exception:
        return None
def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def active_work_item(root: Path) -> str | None:
    data = read_json(root / WORKFLOW_REL)
    if not isinstance(data, dict):
        return None
    raw = data.get('work_item')
    item = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
    value = data.get('active_workflow') or item.get('id')
    return value if isinstance(value, str) else None
def active_workflow_id(root: Path) -> str | None:
    data = read_json(root / WORKFLOW_REL)
    if not isinstance(data, dict):
        return None
    value = data.get('active_workflow')
    return str(value) if isinstance(value, str) and value.strip() else None
def now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)
def parse_iso(s: str) -> _dt.datetime | None:
    try:
        return _dt.datetime.fromisoformat(s)
    except Exception:
        return None
def repo_file(root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        return None
    value = relative.replace('\\', '/').strip()
    if value.startswith('/') or re.match('^[A-Za-z]:/', value) or Path(value).is_absolute() or (value == '..') or value.startswith('../'):
        return None
    candidate = (root / value).resolve()
    if candidate != root and root not in candidate.parents:
        return None
    return candidate if candidate.is_file() else None
def scope_digest(root: Path, scope: object) -> str:
    paths = sorted({str(item).replace('\\', '/') for item in cast(list[object], scope) if isinstance(item, str)}) if isinstance(scope, list) else []
    digest = hashlib.sha256()
    for relative in paths:
        path = repo_file(root, relative)
        if path is None:
            return ''
        digest.update(relative.encode('utf-8'))
        digest.update(b'\x00')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b'\n')
    return digest.hexdigest()
def report_pass(root: Path, relative: object) -> bool:
    path = repo_file(root, relative)
    if path is None:
        return False
    content = path.read_text(encoding='utf-8', errors='replace')
    match = re.search('^status:\\s*([^\\s]+)', content, re.IGNORECASE | re.MULTILINE)
    return bool(match and match.group(1).upper() == 'PASS')
def explicit_authorization(root: Path) -> tuple[bool | None, str]:
    auth = read_json(root / AUTH_REL)
    if not isinstance(auth, dict):
        return (None, '')
    if not auth.get('authorized'):
        return (False, 'explicit authorization present but authorized=false')
    active = active_workflow_id(root)
    auth_wi = auth.get('work_item')
    if not active:
        return (False, 'explicit authorization has no active workflow')
    if auth_wi != active:
        return (False, f'explicit authorization is for {auth_wi} but active work item is {active}')
    bp = auth.get('blueprint_path')
    blueprint_path = repo_file(root, bp)
    if blueprint_path is None:
        return (False, f'explicit authorization blueprint is not a repo-relative file: {bp}')
    if not is_canonical_blueprint_path(root, blueprint_path):
        return (False, f'explicit authorization blueprint is not canonical: {bp}')
    blueprint_hash = auth.get('blueprint_sha256')
    if not isinstance(blueprint_hash, str) or blueprint_hash != sha256_file(blueprint_path):
        return (False, 'explicit authorization Blueprint hash is stale or missing')
    exp = auth.get('expires_at')
    if exp:
        dt = parse_iso(exp) if isinstance(exp, str) else None
        if dt is None or dt.tzinfo is None or dt < now():
            return (False, f'explicit authorization expired at {exp}')
    return (True, f'explicit authorization for {auth_wi} (blueprint: {bp})')
def state_authorization(root: Path) -> tuple[bool, str]:
    wf = read_json(root / WORKFLOW_REL)
    if not isinstance(wf, dict):
        return (False, 'no workflow.json — run /aiwf to start a workflow')
    runtime = read_json(root / '.agents' / 'state' / 'runtime.json') or {}
    status = str(wf.get('status') or runtime.get('status') or '').upper()
    if status not in ('IN_PROGRESS', 'ACTIVE', 'WAITING_INPUT'):
        return (False, f"no active workflow (status={status or 'missing'})")
    active = active_workflow_id(root)
    phase = str(wf.get('active_phase') or wf.get('phase') or '').lower()
    if phase not in IMPLEMENTATION_PHASES:
        return (False, f"workflow phase '{phase or 'unknown'}' is before implementation — generate and APPROVE the Technical Blueprint first (/aiwf)")
    approval_path = root / APPROVALS_REL
    if active:
        scoped_path = root / '.agents' / 'state' / 'work-items' / str(active) / 'approvals.json'
        if scoped_path.exists():
            approval_path = scoped_path
    ap = read_json(approval_path) or {}
    raw_bp = ap.get('blueprint')
    bp = cast(dict[str, object], raw_bp) if isinstance(raw_bp, dict) else None
    if not isinstance(bp, dict) or not bp.get('approved'):
        return (False, f'blueprint not approved in {approval_path.relative_to(root).as_posix()}')
    path = bp.get('path')
    if not path:
        return (False, f'{approval_path.relative_to(root).as_posix()} blueprint has no path')
    blueprint_path = repo_file(root, path)
    if blueprint_path is None or not is_canonical_blueprint_path(root, blueprint_path):
        return (False, f'approved blueprint doc not found on disk: {path}')
    if active and active not in str(path):
        return (False, f"approved blueprint '{path}' is not for active work item {active} (stale approval) — re-approve a blueprint for this work item")
    gate_ok, gate_reason = code_block_gate_authorization(root, active, str(path))
    if not gate_ok:
        return (False, gate_reason)
    return (True, f'authorized via state: {active} phase={phase} (blueprint: {path})')
def code_block_gate_authorization(root: Path, active: str | None, blueprint_path: str) -> tuple[bool, str]:
    blueprint_abs = root / blueprint_path
    try:
        frontmatter = blueprint_abs.read_text(encoding='utf-8').split('---', 2)
    except OSError as exc:
        return (False, f"cannot read approved blueprint '{blueprint_path}': {exc}")
    if len(frontmatter) >= 2:
        for line in frontmatter[1].splitlines():
            key, separator, value = line.partition(':')
            if separator and key.strip().lower() == 'code_block_gate':
                if value.strip().upper() in {'NOT_APPLICABLE', 'N/A', 'NONE'}:
                    return (True, f'strict CODE_BLOCK_GATE not applicable ({blueprint_path})')
                break
    candidates = [root / CODE_BLOCK_GATE_STATE_REL]
    if active:
        candidates.append(root / 'docs' / 'aiwf-runs' / active / '05-blueprint' / 'code-block-gate.json')
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return (False, 'missing canonical code-block-gate.json — run strict-code-block-gate for the approved Blueprint')
    try:
        blueprint_hash = sha256_file(blueprint_abs)
    except OSError as exc:
        return (False, f"cannot hash approved blueprint '{blueprint_path}': {exc}")
    reasons: list[str] = []
    for gate_path in existing:
        result = read_json(gate_path)
        if not isinstance(result, dict):
            reasons.append(f'{gate_path}: invalid JSON')
            continue
        decision = str(result.get('decision') or result.get('status') or '').upper()
        if decision != 'PASS':
            reasons.append(f"{gate_path}: decision is {decision or 'missing'}, expected PASS")
            continue
        if result.get('authority') not in (None, 'strict-code-block-gate'):
            reasons.append(f'{gate_path}: authority is not strict-code-block-gate')
            continue
        result_blueprint = str(result.get('blueprint_path') or blueprint_path)
        if result_blueprint.replace('\\', '/') != blueprint_path.replace('\\', '/'):
            reasons.append(f'{gate_path}: blueprint_path does not match approved blueprint')
            continue
        result_hash = result.get('blueprint_full_sha256') or result.get('blueprint_artifact_hash')
        if result_hash != blueprint_hash:
            reasons.append(f'{gate_path}: blueprint hash is stale')
            continue
        blocked = result.get('blocking_findings')
        if blocked:
            reasons.append(f'{gate_path}: blocking_findings is not empty')
            continue
        for key in ('per_code_block', 'profile_results'):
            raw_rows = result.get(key, [])
            rows = cast(list[object], raw_rows) if isinstance(raw_rows, list) else []
            bad = any((isinstance(item, dict) and str(cast(dict[str, object], item).get('status', '')).upper() in ('FAIL', 'BLOCKED') for item in rows))
            if bad:
                reasons.append(f'{gate_path}: {key} contains FAIL/BLOCKED')
                break
        else:
            return (True, f'strict CODE_BLOCK_GATE PASS ({gate_path.relative_to(root)})')
    return (False, 'strict CODE_BLOCK_GATE not valid: ' + '; '.join(reasons))
def is_canonical_blueprint_path(root: Path, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    return bool(re.match('^docs/features/[^/]+/blueprints/[^/]+(?:_blueprint|-blueprint)\\.md$', relative, re.IGNORECASE) or re.match('^docs/features/[^/]+/blueprints/master/[^/]+(?:_blueprint|-blueprint)\\.md$', relative, re.IGNORECASE) or re.match('^docs/blueprints/[^/]+(?:_blueprint|-blueprint)\\.md$', relative, re.IGNORECASE))
def source_authorization_status(root: Path) -> tuple[bool, str]:
    from .repository import JsonCapabilityRepository
    if JsonCapabilityRepository(root).scoped:
        return False, 'Scoped mode requires a per-file capability decision'
    explicit, reason = explicit_authorization(root)
    return (explicit, reason) if explicit is not None else state_authorization(root)
