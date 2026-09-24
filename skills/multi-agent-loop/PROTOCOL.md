# Multi-Agent Loop — Deterministic Protocol (Engine-Parity Fallback)

Hand-execution fallback for the MALO orchestrator when `scripts/malo` cannot run.
Results MUST match the engine (`scripts/malo/`); the loop-controller
(`skills/loop-controller`) remains the transition authority.

> Foreground, turn-driven. No daemon. All state is files under `.agents/`.

## 1. Per-cycle contract (repeat until HALT or approval gate)
For the current `phase`:
1. **Approval gate?** If `phase ∈ approval_gate_phases` (default `blueprint`,
   `implementation`) → **STOP** with `AWAITING_APPROVAL`; do NOT spawn any agent.
   Ask the user to approve via the normal AIWF flow; resume afterwards.
2. **SELECT agent** — from `.agents/config/agent-registry.json`:
   - candidates = agents where `enabled` and `phase ∈ capabilities`.
   - pick: highest `priority`, then least-recently-used (this run), then lexical `id`.
   - none → **STOP** with `NEEDS_SESSION_AGENT` (run the phase in the current session).
3. **EXECUTE (headless)** — render the agent `invocation` argv, substituting `${task}`,
   `${workflow}`, `${phase}` per element (never build a shell string). Run it in the
   repo root; capture exit code + stdout.
   - Example templates (registry-declared): `claude -p "<task>" --output-format text`;
     `codex exec --skip-git-repo-check "<task>"`; `agy --print "<task>"`.
4. **EVALUATE** — verdict: `exit != 0 → ERROR`; else the first of `FAIL`, `BLOCK`, `PASS`
   found in stdout (precedence in that order); else `BLOCK`.
5. **DECIDE** — hand the verdict + findings to the loop-controller (PROTOCOL of
   `skills/loop-controller`): `aiwf loop decide … --verdict <V> [--finding …]
   [--next-phase <p>] [--backtrack-target <p>] [--terminal]`.
6. **PERSIST** — `aiwf loop persist` the decision, then append one run-ledger row
   `{schema:aiwf.phase-run/1, workflow_id, phase, agent_id, agent_type, verdict,
   exit_code, duration_s, command_redacted, findings, evidence_refs, ts}` to
   `.agents/state/loop/<workflow-id>.runs.jsonl` (append-only; redact the task; no
   absolute paths).
7. **Transition** — `HALT` with `GATE_PASS_FINAL` → `COMPLETED`; `HALT` with
   `NO_PROGRESS`/`MAX_ITERATIONS` → `HALTED_ESCALATE` (present 2–3 options); other
   `HALT` → `HALTED`; else continue at `resulting_phase`.

## 2. Equivalent engine commands
```bash
aiwf malo select --workflow <id> --phase <phase>
aiwf malo run    --workflow <id> --phases <p1,p2,...> [flags]
# launcher fallback: skills/multi-agent-loop/scripts/malo.sh run ...
```

## 3. Invariants
- Never spawn an agent to satisfy an approval gate.
- One active phase per cycle = one writer (MODE_B single-writer).
- The loop-controller — not MALO — owns `{ADVANCE, REPEAT, BACKTRACK, HALT}`.
