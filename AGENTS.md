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

AI_RULES.md is the **single source of truth** for all shared framework behavior. If any instruction conflicts with another document, follow AI_RULES.md.

GitHub Repository: https://github.com/your-org/AI-Agent-Workflow

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

Inspect anytime with the canonical cross-project launcher: `aiwf gate status`.
Do not construct `python tools/aiwf-hooks/aiwf_gate.py ...` from a target
project; bridge-mode projects intentionally may not contain a copied `tools/`
tree. If the installed `aiwf` command is unavailable, use the project bridge
fallback `python .agents/aiwf-hooks/aiwf_gate.py status`. (An explicit override
file via `... authorize` exists for emergencies/bootstrap only.)

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


<!-- AIWF:LOOP-CONTROLLER:BEGIN (hand-maintained) -->
## Self-correcting loop controller

The linear AIWF pipeline runs under a **bounded self-correcting loop**
(`skills/loop-controller`). Each cycle is turn-driven (no daemon): LOAD →
EXECUTE (a phase skill) → EVALUATE (a gate verdict) → DECIDE one of
`{ADVANCE, REPEAT, BACKTRACK, HALT}` → PERSIST. Hard stop-conditions guarantee
termination: `MAX_ITERATIONS` (default 8), `NO_PROGRESS` (same failure signature
×3), `GATE_PASS_FINAL`, `USER_HALT`, `UNRECOVERABLE_ERROR`. A failed
risk-assumption **Spike** (`plan-to-blueprint` §8.1) routes `BACKTRACK` to
`brainstorming`; spike code is throwaway.

Run one cycle (Windows / Linux / macOS — pick the first that is available):

- **Canonical (all tools/OS):** `aiwf loop load|decide|persist ...` — the `aiwf`
  wrapper resolves the interpreter (POSIX `bootstrap.sh`, Windows `bootstrap.ps1`,
  or the bundled `aiwf.exe`).
- **No `aiwf` CLI:** `skills/loop-controller/scripts/loop_engine.sh` (Linux/macOS/
  Git-Bash) or `loop_engine.ps1` (Windows PowerShell 5.1 / pwsh 7) — both
  auto-detect `python3` → `python` → `py -3` (Python ≥ 3.9).
- **No interpreter at all:** read `skills/loop-controller/PROTOCOL.md` and run the
  transition table by hand. All paths produce identical state.

State lives in `.agents/state/loop/<workflow-id>.json` (+ `.ledger.jsonl`).
<!-- AIWF:LOOP-CONTROLLER:END -->


<!-- AIWF:MULTI-AGENT-LOOP:BEGIN (hand-maintained) -->
## Multi-agent loop orchestration

`skills/multi-agent-loop` drives the loop with **multiple heterogeneous agents**
(Claude, Codex, Antigravity) spawned **headless per phase** on one shared workspace,
until HALT. It is a **foreground** orchestrator (no daemon) that reuses the
loop-controller (transition authority) and devteam (shared-workspace mailbox).

- **Assignment is dynamic by capability**: `.agents/config/agent-registry.json`
  (`aiwf.agent-registry/1`) declares each agent's `type`, `priority`, `capabilities`
  (phases) and headless `invocation`. The engine selects per phase (priority → LRU → id).
  Codex needs `--skip-git-repo-check` outside a git repo (default registry includes it).
- **Continuous run, human gates preserved**: auto-runs through non-approval phases; at
  Blueprint/Implementation approval it HALTs (`AWAITING_APPROVAL`) — agents are never
  spawned to approve. After the user approves, re-running resumes from loop-state.

Run (Windows / Linux / macOS):
```bash
aiwf malo run --workflow <id> --phases plan,blueprint,implement,verify
# no aiwf CLI: skills/multi-agent-loop/scripts/malo.sh run ...  (or malo.ps1 on Windows)
# no interpreter: skills/multi-agent-loop/PROTOCOL.md by hand
```
Run ledger: `.agents/state/loop/<workflow-id>.runs.jsonl` (`aiwf.phase-run/1`).
No registry → the current session agent runs every phase (backward compatible).
<!-- AIWF:MULTI-AGENT-LOOP:END -->





