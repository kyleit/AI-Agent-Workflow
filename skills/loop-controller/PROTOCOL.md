# Loop Controller — Deterministic Protocol (Engine-Parity Fallback)

This document is the **hand-execution fallback** for the AIWF Loop Controller.
When the deterministic engine (`loop_engine`) cannot be run, the host agent
MUST follow this protocol by hand. The result **MUST be identical** to what the
engine produces — the engine in `scripts/loop_engine/` is the single source of
truth and this table mirrors `domain/transitions.py` + `domain/stop_conditions.py`.

> No daemon, no server, no background process. Every step is one turn-driven
> invocation reading/writing files under `.agents/state/loop/`.

---

## 1. Controller contract — 5 steps per invocation

| Step | Name | Who | Action |
|---|---|---|---|
| 1 | **LOAD** | engine/agent | Read `loop_state` + Bootstrap Receipt. If `loop_state` missing → initialize `iteration=0` (backward compatible). If Bootstrap Receipt missing → require `initialize-workflow`. |
| 2 | **EXECUTE** | agent | Run the skill of `current_phase` (this is an agent turn; the engine never runs a skill). |
| 3 | **EVALUATE** | gate/skill | Obtain a verdict from `readiness-and-approval-gates` / test-gate / spike-gate and the list of blocking findings. |
| 4 | **DECIDE** | engine/agent | Compute exactly one transition ∈ `{ADVANCE, REPEAT, BACKTRACK, HALT}` using §3. |
| 5 | **PERSIST** | engine/agent | Atomically write the new `loop_state`, append one ledger line, and record the receipt via `workflow-command-audit`. |

## 2. Inputs to DECIDE

- `state`: current `loop_state` (`iteration`, `max_iterations`, `failure_signature`, `no_progress_count`, `no_progress_threshold`, `current_phase`).
- `verdict` ∈ `{PASS, BLOCK, FAIL, ERROR}` — map gate decisions:
  `PASS→PASS`; `BLOCKED|AWAITING_APPROVAL|INVALIDATED→BLOCK`; `FAIL→FAIL`; unrecoverable runtime error `→ERROR`.
- `new_failure_signature`: SHA-256 over the normalized (trim → lowercase → dedupe → sort) blocking findings; empty string when there are none.
- Flags: `approval_present`, `requires_approval`, `is_terminal_phase`, `user_halt`.
- `next_phase`: the downstream phase per the existing handoff order.
- `backtrack_target`: the phase a named failure points to (e.g. spike `fail → brainstorming`).

## 3. Decision algorithm (exact order — do not reorder)

```
candidate_iteration = state.iteration + 1

# projected no-progress counter
if verdict == PASS:
    projected_no_progress = 0
elif new_failure_signature != "" and new_failure_signature == state.failure_signature:
    projected_no_progress = state.no_progress_count + 1
else:
    projected_no_progress = 0

approval_ok = (not requires_approval) or approval_present

# collect stop-conditions (any that hold)
stops = []
if user_halt:                                        stops += [USER_HALT]
if verdict == ERROR:                                 stops += [UNRECOVERABLE_ERROR]
if candidate_iteration >= state.max_iterations:      stops += [MAX_ITERATIONS]
if projected_no_progress >= state.no_progress_threshold: stops += [NO_PROGRESS]
if verdict == PASS and approval_ok and is_terminal_phase: stops += [GATE_PASS_FINAL]

if stops:
    transition       = HALT
    resulting_phase  = state.current_phase
    next_iteration   = candidate_iteration
    no_progress_count= projected_no_progress
    backtrack_target = null
    escalate         = (NO_PROGRESS in stops) or (MAX_ITERATIONS in stops)
else:
    if verdict == PASS and not approval_ok:
        transition = REPEAT;  resulting_phase = state.current_phase
        next_iteration = candidate_iteration;  no_progress_count = projected_no_progress
    elif verdict == PASS:
        transition = ADVANCE; resulting_phase = next_phase
        next_iteration = 0;   no_progress_count = 0
    elif verdict == FAIL and backtrack_target:
        transition = BACKTRACK; resulting_phase = backtrack_target
        next_iteration = 0;     no_progress_count = projected_no_progress
        backtrack_target = backtrack_target
    else:  # BLOCK, or FAIL without a target
        transition = REPEAT;  resulting_phase = state.current_phase
        next_iteration = candidate_iteration;  no_progress_count = projected_no_progress
```

### Transition summary table

| verdict | condition | transition | resulting_phase | next_iteration | no_progress |
|---|---|---|---|---|---|
| any | `user_halt` | HALT (`USER_HALT`) | same | candidate | projected |
| ERROR | — | HALT (`UNRECOVERABLE_ERROR`) | same | candidate | projected |
| any | `candidate ≥ max_iterations` | HALT (`MAX_ITERATIONS`, escalate) | same | candidate | projected |
| non-PASS | `projected ≥ threshold` | HALT (`NO_PROGRESS`, escalate) | same | candidate | projected |
| PASS | `approval_ok` & terminal | HALT (`GATE_PASS_FINAL`) | same | candidate | 0 |
| PASS | `approval_ok` & not terminal | ADVANCE | `next_phase` | 0 | 0 |
| PASS | `not approval_ok` | REPEAT | same | candidate | projected |
| FAIL | `backtrack_target` set | BACKTRACK | `backtrack_target` | 0 | projected |
| BLOCK / FAIL | no target | REPEAT | same | candidate | projected |

> Stop-conditions are checked **before** the verdict branch and win. Multiple
> stop-conditions may be reported together; escalation fires for `NO_PROGRESS`
> or `MAX_ITERATIONS`.

## 4. Stop-conditions (anti-infinite-loop)

1. `MAX_ITERATIONS` — `iteration + 1 ≥ max_iterations` (default `max_iterations = 8`).
2. `GATE_PASS_FINAL` — final-phase gate PASS + valid approval.
3. `NO_PROGRESS` — identical `failure_signature` for `no_progress_threshold` consecutive cycles (default `3`) → HALT and **escalate to the user with 2–3 options**.
4. `USER_HALT` — explicit user halt.
5. `UNRECOVERABLE_ERROR` — non-recoverable runtime error.

On escalation, present: (a) BACKTRACK to a named upstream phase, (b) REVISE inputs / narrow scope then REPEAT, (c) CANCEL the workflow.

## 5. PERSIST — next `loop_state` fields

Set on every decision: `last_verdict = verdict`, `failure_signature = new_failure_signature`,
`transition`, `backtrack_target` (only for BACKTRACK, else `null`),
`stop_conditions_met`, `iteration = next_iteration`, `no_progress_count`,
`updated_at = <ISO-8601 UTC>` (stamped at persist). Then append one ledger line
`{iter, phase, action, gate, verdict, evidence_refs[], next, ts}` to
`.agents/state/loop/<workflow-id>.ledger.jsonl` (append-only) and record the
command receipt via `workflow-command-audit`.

## 6. Invoking the engine — three layers (interpreter-agnostic)

The controller never assumes a specific interpreter name. Use, in order of
preference:

**Layer 1 — canonical (agent-facing).** Same as every other AIWF skill; the
installed `aiwf` wrapper resolves the interpreter for you:
```bash
aiwf loop load    --workflow <id> --phase <phase>
aiwf loop decide  --workflow <id> --phase <phase> --verdict <PASS|BLOCK|FAIL|ERROR> [flags]
aiwf loop persist --input <decide-output.json | ->
```

**Layer 2 — portable launcher (no `aiwf` CLI installed).** Auto-detects
`python3` → `python` → `py -3` (requires Python ≥ 3.9); on failure it prints a
`NoPythonInterpreter` envelope and exits `3`, telling you to use Layer 3:
```bash
# POSIX shell (Linux/macOS/Git-Bash — the shell Claude Code/Codex/Antigravity use):
skills/loop-controller/scripts/loop_engine.sh decide --workflow <id> --phase <phase> --verdict FAIL --backtrack-target brainstorming
# Windows PowerShell / pwsh:
skills/loop-controller/scripts/loop_engine.ps1 decide --workflow <id> --phase <phase> --verdict FAIL --backtrack-target brainstorming
# Maintainer/debug direct form (only when the interpreter name is known):
#   PYTHONPATH=skills/loop-controller/scripts <python> -m loop_engine <...>
```
Full flag set for `decide`: `[--finding "<blocker>" ...] [--approval-present]
[--requires-approval] [--terminal] [--next-phase <p>] [--backtrack-target <p>]
[--user-halt] [--gate <name>] [--evidence <ref> ...] [--repo-root <root>]`.

**Layer 3 — no interpreter at all.** Execute §3 by hand and write the files in
§5 directly. This is the ultimate fallback and produces identical results.

`load` and `decide` never write; `persist` performs the only side effects.
`aiwf loop <...>`, the launchers, and hand-execution are all equivalent.
