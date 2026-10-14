# AIWF Source-Write Gate

Deterministic, tool-agnostic enforcement that **no source code changes until an
AIWF Technical Blueprint is approved** for the active work item. Blocks smart or
dumb models, thinking or not, in any AI editor.

## Files

| File | Role |
|------|------|
| `aiwf_gate.py` | Decision core (source detection + authorization). Shared by all hooks. |
| `claude_source_write_guard.py` | Claude PreToolUse guard (in-repo copy). |
| `../githooks/pre-commit` | Blocks committing unauthorized source (universal). |
| `../githooks/pre-push` | Backstop for `--no-verify` (universal). |
| `~/.claude/hooks/aiwf-source-write-guard.py` | Global Claude launcher (delegates to this repo's `aiwf_gate.py`). |

## Enable (per clone)

```bash
git config core.hooksPath tools/githooks
chmod +x tools/githooks/pre-commit tools/githooks/pre-push
```

The Claude PreToolUse hook is registered once in `~/.claude/settings.json` under
`hooks.PreToolUse` matcher `Edit|Write|MultiEdit|NotebookEdit`. It self-gates:
non-AIWF projects pass through.

## Concurrent Work Items

The global `workflow.json` is display focus, not a repository-wide source lock.
Each approved FEAT/FIX/QUICK receives an authoritative capability at
`.agents/state/work-items/<id>/implementation-entry-receipt.json` when
`aiwf implement --blueprint <path> --work-item <id>` enters implementation.
The runtime verifies the current approval, complete master/phase artifact set,
exact recursive file matrix, machine gate, owner/session and project identity.
No separate human approval is needed for unchanged 24-hour renewal.

An edit is allowed only when exactly one valid item owns that file. Two items
may work on disjoint files simultaneously. Shared files report `SCOPE_CONFLICT`
with both owners; their nonshared files remain available. Explicit context never
falls back to another item. Invalid, expired or revoked items cannot grant scope.
Use `AIWF_WORK_ITEM_ID` (or `check-file --work-item`) to name an edit context.
Runtime store instances keep their root and item fixed, including factory caches.

Claude batches check every explicit target. Git checks deletions and both rename
endpoints with NUL-delimited names. `check-outgoing` receives actual pre-push
ref lines and requires evidence for every outgoing commit/path, not one earlier
change to the same file. Git inspection failures deny instead of allowing an
empty batch. Release/tag authority stays separate and never unlocks source edits.

`aiwf gate status` reports item health; a status summary is not a file permission.
`revoke --work-item <id>` revokes just that item. Once scoped mode is activated,
missing/invalid scoped receipts cannot fall back to legacy global approval.
The `source_gate/` family is recursively distributed beside the stable facade.

## Legacy Entry (Before Scoped Activation)

The gate derives authorization from AIWF workflow state. Source writes unlock
when ALL hold for the active work item:

1. `.agents/state/workflow.json` → `status` IN_PROGRESS and `active_phase` is an
   implementation phase (implementation / debug / verification / release).
2. `.agents/state/approvals.json` → `blueprint.approved == true` and
   `blueprint.path` exists on disk.
3. The active work item id appears in the blueprint path (binds the approval to
   the task, so a stale approval can't unlock a different one).

So the ONLY action required is the normal /aiwf flow: generate + approve the
blueprint. Approval advances the phase → the gate opens by itself. Nobody (not
the user, not the AI) runs an unlock command.

## CLI (inspection + emergency override)

```bash
aiwf gate status                                                   # AI/IDE canonical entrypoint

# Legacy bridge fallback when the installed command is unavailable:
python .agents/aiwf-hooks/aiwf_gate.py status                      # show gate state

python .agents/aiwf-hooks/aiwf_gate.py check-file <path>           # exit 0 allow / 1 block
python .agents/aiwf-hooks/aiwf_gate.py check-git                   # staged files (pre-commit)

```

Do not construct `python tools/aiwf-hooks/aiwf_gate.py ...` inside an
installed project. That relative path is valid only from the framework source
repository. Bridge-mode projects intentionally do not contain a copied
`tools/` tree; `aiwf gate status` resolves the authoritative global gate and
keeps the project root isolated.

```bash

# Emergency / bootstrap ONLY — explicit override file (normally unused):
python .agents/aiwf-hooks/aiwf_gate.py authorize --blueprint docs/features/<id>/blueprint.md [--ttl-hours 24]
python .agents/aiwf-hooks/aiwf_gate.py revoke
```

## Emergency bypass

```bash
AIWF_BYPASS=1 git commit ...      # logged to stderr
```

See `docs/features/source-write-gate/README.md` for FEAT-618 design and evidence.
