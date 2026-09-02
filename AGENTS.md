<!-- AIWF:RULES:BEGIN -->
# AI Engineering Workflow Agents

Every AI agent working inside this project **MUST** follow the AI Workflow Framework.

## Primary Workflow

Before executing any task:

1. Load and follow all policies defined in AI_RULES.md (the single source of truth).
2. Load the workflow resources from:

   * .agents/skills/
   * .agents/runtime/
   * .agents/templates/
3. Use the matching workflow Skill whenever one exists.
4. Respect runtime checkpoints and resume rules.
5. Never bypass approval gates or other framework policies.

## Global Policies

The following policies are defined in AI_RULES.md and apply to every task:

1. Approval Gate Policy
2. Git Workflow Policy
3. Memory First Policy
4. RAG Policy
5. Artifact Policy
6. Versioning Policy
7. Documentation Policy
8. Testing Policy
9. Release Policy
10. Workflow Phase Separation Policy
11. Absolute Path Prohibition Policy
12. Global Multi-Language Strict Engineering Policy
13. Physical Repository Write Policy & Disk Mutation Verification Gate

AI_RULES.md is the **single source of truth** for all shared framework behavior. If any instruction conflicts with another document, follow AI_RULES.md.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow.git

This public repository URL is intentional source configuration. AI agents must
not replace, remove, redact, or silently substitute it with a placeholder.

<!-- AIWF:RULES:END -->

<!-- AIWF:SOURCE-WRITE-GATE:BEGIN (hand-maintained; survives `aiwf update`) -->
## MANDATORY: Route source changes through /aiwf

Any request that adds/changes/fixes a feature or otherwise **modifies source
code** MUST go through the AIWF workflow BEFORE editing code — regardless of
whether the user typed `/aiwf` or invoked any skill:

1. `/aiwf <request>` → `initialize-workflow` → `workflow-coordinator`
2. Produce Spec → Technical Blueprint (`docs/features/...`)
3. Get the Blueprint approved (Blueprint Approval Gate)
4. Only then edit source code.

This is **enforced deterministically**, not by trust:

- **Git `pre-commit` / `pre-push` hooks** (`core.hooksPath = tools/githooks`)
  block committing/pushing source changes until the workflow is authorized.
  Applies to EVERY AI/editor.
- **Claude Code `PreToolUse` hook** blocks source edits at write-time.

**Unlocking is automatic — nobody runs a command.** The gate reads AIWF workflow
state (`.agents/state/workflow.json` + `approvals.json`). Source writes unlock
once, for the active work item: the blueprint is approved AND the workflow has
entered an implementation phase. Approving the blueprint via the normal /aiwf
flow is all that is required; the approval is bound to the active work item so a
stale approval never unlocks a different task.

Inspect anytime: `python .agents/aiwf-hooks/aiwf_gate.py status`. (An explicit
override file via `... authorize` exists for emergencies/bootstrap only.)

Docs (`docs/`, `*.md`), mirrors (`.agents/`, `public_export/`) and the gate
tooling itself are never gated. Emergency bypass (agent/CI only, logged):
`AIWF_BYPASS=1`.
<!-- AIWF:SOURCE-WRITE-GATE:END -->


<!-- AIWF:DEVTEAM:BEGIN (hand-maintained) -->
## DevTeam multi-session seats

This repo can be split across **seats** (a leader + N dev-seats), each owning one
slice of the repo and coordinating through file mailboxes. To take a seat:

- If your tool has the adapter: run its `/seat <slug>` (Claude), the `seat` skill
  (Codex), or the DevTeam workflow (Antigravity) — one action.
- Otherwise: read `docs/features/agent-orchestration/PROTOCOL.md` and follow it
  with your own file tools. All paths produce identical files, so any tool can
  occupy any seat.

Engine (global, all tools): `python -m devteam init|seat|mailbox|board`.
Data lives in `.agents/devteam/` (roster, charters, state, board) and
`.agents/session-mail/` (inboxes). Never edit another seat's write-set.
<!-- AIWF:DEVTEAM:END -->





