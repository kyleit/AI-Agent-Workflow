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

## How it unlocks (automatic — no command)

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
python tools/aiwf-hooks/aiwf_gate.py status                       # show gate state
python tools/aiwf-hooks/aiwf_gate.py check-file <path>            # exit 0 allow / 1 block
python tools/aiwf-hooks/aiwf_gate.py check-git                    # staged files (pre-commit)

# Emergency / bootstrap ONLY — explicit override file (normally unused):
python tools/aiwf-hooks/aiwf_gate.py authorize --blueprint docs/features/<id>/blueprint.md [--ttl-hours 24]
python tools/aiwf-hooks/aiwf_gate.py revoke
```

## Emergency bypass

```bash
AIWF_BYPASS=1 git commit ...      # logged to stderr
```

See `docs/features/aiwf-source-write-gate/blueprint.md` for the full design.
