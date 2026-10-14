#!/usr/bin/env python3
"""Stable AIWF source gate facade; implementations live in source_gate."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_gate.legacy import (
    repo_root as repo_root,
    is_aiwf_project as is_aiwf_project,
    rel_posix as _rel_posix,
    repo_relative as _repo_relative,
    is_source_file as is_source_file,
    read_json as _read_json,
    sha256_file as _sha256_file,
    active_work_item as active_work_item,
    active_workflow_id as _active_workflow_id,
    now as _now,
    parse_iso as _parse_iso,
    repo_file as _repo_file,
    scope_digest as _scope_digest,
    report_pass as _report_pass,
    explicit_authorization as _explicit_authorization,
    state_authorization as _state_authorization,
    code_block_gate_authorization as _code_block_gate_authorization,
    is_canonical_blueprint_path as _is_canonical_blueprint_path,
    source_authorization_status as _source_authorization_status,
    SOURCE_EXTS as SOURCE_EXTS,
    EXCLUDED_PREFIXES as EXCLUDED_PREFIXES,
    AUTH_REL as AUTH_REL,
    WORKFLOW_REL as WORKFLOW_REL,
    APPROVALS_REL as APPROVALS_REL,
    CODE_BLOCK_GATE_STATE_REL as CODE_BLOCK_GATE_STATE_REL,
    AIWF_MARKER_REL as AIWF_MARKER_REL,
    IMPLEMENTATION_PHASES as IMPLEMENTATION_PHASES,
)
from source_gate.release import (
    release_authorization_status as _release_authorization_status,
    receipt_dir as _receipt_dir,
    RELEASE_AUTH_REL as RELEASE_AUTH_REL,
)
from source_gate.git_changes import (
    git_lines as _git_lines,
    outgoing_commits as _outgoing_commits,
    commit_parents as _commit_parents,
    commit_touches_file as _commit_touches_file,
    authorization_receipts as _authorization_receipts,
    receipt_authorizes as _receipt_authorizes,
    is_commit_or_history_authorized as _is_commit_or_history_authorized,
)
from source_gate.commands import (
    cmd_check_git as cmd_check_git,
    cmd_check_files as cmd_check_files,
    cmd_check_outgoing as cmd_check_outgoing,
    cmd_check_release_tags as cmd_check_release_tags,
    cmd_check_file as cmd_check_file,
    cmd_authorize as cmd_authorize,
    cmd_revoke as cmd_revoke,
    cmd_status as cmd_status,
    build_parser as build_parser,
    main as _command_main,
    BLOCK_BANNER as BLOCK_BANNER,
    HELP_TEXT as HELP_TEXT,
    bypassed as _bypassed,
    authorization_status as authorization_status,
    check_paths as check_paths,
)
from source_gate import authorize_paths as authorize_paths, issue_capability as issue_capability
from source_gate.git_changes import staged_changes
from source_gate.commands import bypassed as bypassed
from source_gate.commands import describe_decision as describe_decision

__all__ = ["repo_root","is_aiwf_project","_rel_posix","_repo_relative","is_source_file","_read_json","_sha256_file","active_work_item","_active_workflow_id","_now","_parse_iso","_repo_file","_scope_digest","_report_pass","_explicit_authorization","_state_authorization","_code_block_gate_authorization","_is_canonical_blueprint_path","_source_authorization_status","SOURCE_EXTS","EXCLUDED_PREFIXES","AUTH_REL","WORKFLOW_REL","APPROVALS_REL","CODE_BLOCK_GATE_STATE_REL","AIWF_MARKER_REL","IMPLEMENTATION_PHASES","_release_authorization_status","_receipt_dir","RELEASE_AUTH_REL","_git_lines","_outgoing_commits","_commit_parents","_commit_touches_file","_authorization_receipts","_receipt_authorizes","_is_commit_or_history_authorized","cmd_check_git","cmd_check_files","cmd_check_outgoing","cmd_check_release_tags","cmd_check_file","cmd_authorize","cmd_revoke","cmd_status","build_parser","main","BLOCK_BANNER","HELP_TEXT","_bypassed","authorization_status","check_paths","authorize_paths","issue_capability","_staged_files","bypassed"]


def _staged_files(root: Path) -> list[str]:
    return [change.path.value for change in staged_changes(root)]


def main(argv: list[str] | None = None) -> int:
    return _command_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
